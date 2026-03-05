import os
import time
import uuid
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.models import (
    AuditRequest, AuditResponse, CategoryResult, IssueSummary,
    CrawlRequest, CrawlResponse, CrawlPageSummary,
    CrawlBrokenLink, CrawlDuplicate,
    PageSpeedResult, SchemaValidationResult,
    KeywordSuggestRequest, KeywordSuggestResponse,
    BrandCreate, BrandUpdate, BrandResponse,
    AuditListItem, AuditDetail, ReportPDFRequest,
)
from app.external_models import ExternalInsights
from app.report import generate_pdf
from app.branded_report import generate_branded_pdf
from app.fetcher import fetch_page
from app.scoring import compute_overall_score
from app.crawler import crawl_site
from app.utils import normalize_domain, check_ssrf
from app.summary import generate_executive_summary
from app.database import get_db, init_db
from app.db_models import Brand, Audit
from app.analyzers import (
    analyze_meta_tags,
    analyze_headings,
    analyze_images,
    analyze_links,
    analyze_performance,
    analyze_mobile,
    analyze_structured_data,
    analyze_sitemap,
    analyze_robots,
    analyze_tracking,
    analyze_semantic,
    analyze_ads_quality,
    analyze_serp_features,
    analyze_accessibility,
    analyze_crawl,
    analyze_schema_validation,
    analyze_pagespeed,
    get_keyword_suggestions,
)
from app.analyzers.traffic_intel import analyze_traffic_intel
from app.analyzers.search_intel import analyze_search_intel
from app.config import (
    EXTERNAL_MODULE_TIMEOUT,
    FEATURE_KEYWORD_PLANNER_ENABLED,
    KEYWORD_PLANNER_ADMIN_TOKEN,
    UPLOAD_DIR,
    UPLOAD_MAX_SIZE_MB,
    UPLOAD_ALLOWED_TYPES,
)

app = FastAPI(title="SEO Auditor", version="2.0.0")

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://deft-pasca-e9b0ab.netlify.app",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving
_static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

    @app.get("/")
    async def serve_dashboard():
        return FileResponse(os.path.join(_static_dir, "index.html"))


# ============================================================
# Core audit logic (unchanged for backward compatibility)
# ============================================================

def _run_analyzer(fn, page, name: str) -> CategoryResult:
    start = time.perf_counter()
    try:
        result = fn(page)
        elapsed = int((time.perf_counter() - start) * 1000)
        summary = IssueSummary(
            error_count=sum(1 for i in result.issues if i.severity == "error"),
            warning_count=sum(1 for i in result.issues if i.severity == "warning"),
            info_count=sum(1 for i in result.issues if i.severity == "info"),
            pass_count=sum(1 for i in result.issues if i.severity == "pass"),
        )
        result.summary = summary
        result.duration_ms = elapsed
        return result
    except Exception as exc:
        elapsed = int((time.perf_counter() - start) * 1000)
        return CategoryResult(
            name=name, score=0, issues=[],
            status="error",
            error_message=str(exc)[:200],
            duration_ms=elapsed,
            summary=IssueSummary(),
        )


@app.post("/api/audit", response_model=AuditResponse)
async def run_audit(req: AuditRequest, db: Session = Depends(get_db)):
    audit_start = time.perf_counter()
    url = str(req.url)

    # Validate save_result + brand_id
    if req.save_result and not req.brand_id:
        raise HTTPException(
            status_code=422,
            detail="brand_id is required when save_result=true. Create a brand first via POST /api/brands."
        )
    if req.brand_id:
        brand = db.query(Brand).filter(Brand.id == req.brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail=f"Brand {req.brand_id} not found.")
    else:
        brand = None

    try:
        page = fetch_page(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch URL: {e}")

    analyzers = [
        (analyze_meta_tags, "meta_tags"),
        (analyze_headings, "headings"),
        (analyze_images, "images"),
        (analyze_links, "links"),
        (analyze_performance, "performance"),
        (analyze_mobile, "mobile"),
        (analyze_structured_data, "structured_data"),
        (analyze_sitemap, "sitemap"),
        (analyze_robots, "robots"),
        (analyze_tracking, "tracking"),
        (analyze_semantic, "semantic"),
        (analyze_ads_quality, "ads_quality"),
        (analyze_serp_features, "serp_features"),
        (analyze_accessibility, "accessibility"),
    ]

    categories: list[CategoryResult] = []
    with ThreadPoolExecutor(max_workers=len(analyzers)) as executor:
        futures = {
            executor.submit(_run_analyzer, fn, page, name): name
            for fn, name in analyzers
        }
        for future in as_completed(futures):
            categories.append(future.result())

    order = [name for _, name in analyzers]
    categories.sort(key=lambda c: order.index(c.name))
    overall = compute_overall_score(categories)

    # --- Schema validation (opt-in) ---
    schema_validation = None
    if req.include_schema_validation:
        try:
            schema_validation = analyze_schema_validation(page)
        except Exception:
            schema_validation = None

    # --- PageSpeed Insights (opt-in) ---
    pagespeed_insights = None
    psi_future = None
    if req.include_pagespeed:
        psi_executor = ThreadPoolExecutor(max_workers=1)
        psi_future = psi_executor.submit(analyze_pagespeed, url)

    # --- External intelligence (opt-in) ---
    external_insights = None
    if req.include_external:
        external_insights = _run_external_intel(url, req.external_modules)

    # --- Site crawl (opt-in) ---
    crawl_results = None
    if req.include_crawl:
        crawl_results = _run_crawl(url, min(req.crawl_max_pages, 50))

    # Collect PSI result
    if psi_future is not None:
        try:
            pagespeed_insights = psi_future.result(timeout=65)
        except Exception:
            pagespeed_insights = None
        psi_executor.shutdown(wait=False)

    # --- Executive summary (opt-in, default true) ---
    executive_summary = None
    if req.include_exec_summary:
        cat_dicts = [c.model_dump() for c in categories]
        executive_summary = generate_executive_summary(
            categories=cat_dicts,
            brand_name=brand.name if brand else None,
            brand_description=brand.description if brand else None,
            overall_score=overall,
        )

    # --- Brand profile (opt-in) ---
    brand_profile = None
    if req.include_public_profile and brand:
        brand_profile = {
            "name": brand.name,
            "primary_domain": brand.primary_domain,
            "industry": brand.industry,
            "description": brand.description,
            "persona": brand.persona,
            "revenue_range": brand.revenue_range,
            "revenue_source": "Provided by client",
            "enrichment_status": brand.enrichment_status_json or {"status": "not_configured"},
        }

    audit_duration = int((time.perf_counter() - audit_start) * 1000)

    # --- Save to DB if requested ---
    audit_id = None
    if req.save_result and brand:
        audit_record = Audit(
            brand_id=brand.id,
            audited_url=url,
            audited_domain=normalize_domain(url),
            overall_score=overall,
            category_results_json={
                "url": url,
                "overall_score": overall,
                "categories": [c.model_dump() for c in categories],
            },
            insights_json=(external_insights.model_dump() if external_insights else None),
            summary_json=executive_summary,
            status="ok",
            duration_ms=audit_duration,
        )
        db.add(audit_record)
        db.commit()
        db.refresh(audit_record)
        audit_id = audit_record.id

    return AuditResponse(
        url=url,
        overall_score=overall,
        categories=categories,
        external_insights=external_insights,
        crawl_results=crawl_results,
        pagespeed_insights=pagespeed_insights,
        schema_validation=schema_validation,
        audit_id=audit_id,
        brand_id=req.brand_id,
        executive_summary=executive_summary,
        brand_profile=brand_profile,
    )


def _run_external_intel(url: str, modules: Optional[list] = None) -> ExternalInsights:
    allowed = {"similarweb", "semrush"}
    requested = set(modules) & allowed if modules else allowed
    domain = normalize_domain(url)
    check_ssrf(domain)

    sw_result = None
    sr_result = None
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}
        if "similarweb" in requested:
            futures[executor.submit(analyze_traffic_intel, domain)] = "similarweb"
        if "semrush" in requested:
            futures[executor.submit(analyze_search_intel, domain)] = "semrush"

        for future in as_completed(futures, timeout=EXTERNAL_MODULE_TIMEOUT):
            name = futures[future]
            try:
                result = future.result()
                if name == "similarweb":
                    sw_result = result
                else:
                    sr_result = result
            except Exception:
                pass

    return ExternalInsights(similarweb=sw_result, semrush=sr_result)


def _run_crawl(url: str, max_pages: int):
    from app.models import CrawlResponse, CrawlPageSummary, CrawlBrokenLink, CrawlDuplicate
    try:
        result = crawl_site(url, max_pages=max_pages)
        crawl_analysis = analyze_crawl(result)
        pages = [
            CrawlPageSummary(
                url=p.url, title=p.title, description=p.description,
                status_code=p.status_code, internal_links=len(p.internal_links),
                depth=p.depth,
            )
            for p in result.pages
        ]
        broken_links = [
            CrawlBrokenLink(source_url=bl.source_url, target_url=bl.target_url, status_code=bl.status_code)
            for bl in result.broken_links
        ]
        duplicate_titles = [
            CrawlDuplicate(value=title, pages=urls)
            for title, urls in result.duplicate_titles.items()
        ]
        duplicate_descriptions = [
            CrawlDuplicate(value=desc, pages=urls)
            for desc, urls in result.duplicate_descriptions.items()
        ]
        return CrawlResponse(
            url=url, pages_crawled=len(result.pages), max_depth=result.max_depth,
            pages=pages, broken_links=broken_links, orphan_pages=result.orphan_pages,
            duplicate_titles=duplicate_titles, duplicate_descriptions=duplicate_descriptions,
            score=crawl_analysis.score, issues=crawl_analysis.issues,
        )
    except Exception:
        return None


@app.post("/api/crawl", response_model=CrawlResponse)
async def run_crawl_endpoint(req: CrawlRequest):
    url = str(req.url)
    max_pages = min(req.max_pages, 50)
    result = _run_crawl(url, max_pages)
    if result is None:
        raise HTTPException(status_code=400, detail="Crawl failed")
    return result


# ============================================================
# PDF report endpoints (old + new)
# ============================================================

@app.post("/api/report/pdf")
async def export_pdf(data: AuditResponse):
    """Legacy endpoint: generate PDF from inline audit data."""
    pdf_bytes = generate_pdf(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=seo-audit-report.pdf"},
    )


@app.post("/api/reports/pdf")
async def export_branded_pdf(req: ReportPDFRequest, db: Session = Depends(get_db)):
    """Generate branded PDF from a saved audit with theme overrides."""
    audit = db.query(Audit).filter(Audit.id == req.audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    # Reconstruct AuditResponse from snapshot
    snapshot = audit.category_results_json or {}
    cats = [CategoryResult(**c) for c in snapshot.get("categories", [])]
    audit_data = AuditResponse(
        url=snapshot.get("url", audit.audited_url),
        overall_score=snapshot.get("overall_score", audit.overall_score),
        categories=cats,
        executive_summary=audit.summary_json,
    )

    # Determine logo path: theme override > brand > None
    logo_path = None
    brand = audit.brand
    theme = {}
    if brand and brand.theme_json:
        theme = brand.theme_json
    if req.theme_overrides:
        theme.update(req.theme_overrides)

    if brand and brand.logo_path:
        full_logo = os.path.join(UPLOAD_DIR, brand.logo_path)
        if os.path.isfile(full_logo):
            logo_path = full_logo

    # Store theme snapshot
    audit.report_theme_snapshot_json = theme
    db.commit()

    pdf_bytes = generate_branded_pdf(audit_data, logo_path=logo_path)
    domain = audit.audited_domain or "site"
    filename = f"seo-audit-{domain}-{audit.created_at.strftime('%Y%m%d') if audit.created_at else 'report'}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ============================================================
# Brand CRUD
# ============================================================

@app.get("/api/brands")
async def list_brands(db: Session = Depends(get_db)):
    brands = db.query(Brand).order_by(Brand.updated_at.desc()).all()
    results = []
    for b in brands:
        audits = db.query(Audit).filter(Audit.brand_id == b.id).order_by(Audit.created_at.desc()).all()
        latest_score = audits[0].overall_score if audits else None
        previous_score = audits[1].overall_score if len(audits) > 1 else None
        results.append(BrandResponse(
            id=b.id, name=b.name, primary_domain=b.primary_domain,
            industry=b.industry, description=b.description,
            persona=b.persona, revenue_range=b.revenue_range,
            logo_path=b.logo_path, theme_json=b.theme_json,
            enrichment_status_json=b.enrichment_status_json,
            created_at=b.created_at.isoformat() if b.created_at else None,
            updated_at=b.updated_at.isoformat() if b.updated_at else None,
            audit_count=len(audits),
            latest_score=latest_score,
            previous_score=previous_score,
        ))
    return results


@app.post("/api/brands", response_model=BrandResponse)
async def create_brand(req: BrandCreate, db: Session = Depends(get_db)):
    brand = Brand(
        name=req.name,
        primary_domain=req.primary_domain,
        industry=req.industry,
        description=req.description,
        persona=req.persona,
        revenue_range=req.revenue_range,
    )
    db.add(brand)
    db.commit()
    db.refresh(brand)

    # Auto-enrich: fetch homepage metadata for fields user didn't provide
    try:
        from app.providers.enrichment.auto_fetch import AutoFetchEnrichmentProvider

        provider = AutoFetchEnrichmentProvider()
        existing_fields = {
            "description": req.description,
            "industry": req.industry,
        }
        enrichment = provider.enrich(brand.primary_domain, existing_fields)

        if enrichment.status == "ok" and enrichment.fields:
            for field_name, value in enrichment.fields.items():
                current = getattr(brand, field_name, None)
                if not current:
                    setattr(brand, field_name, value)
            brand.enrichment_status_json = {
                "auto_fetch": {
                    "status": enrichment.status,
                    "data_source": enrichment.data_source,
                    "fields": list(enrichment.fields.keys()),
                    "confidence": enrichment.confidence,
                }
            }
        else:
            brand.enrichment_status_json = {
                "auto_fetch": {
                    "status": enrichment.status,
                    "error_message": enrichment.error_message,
                }
            }
        brand.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(brand)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Auto-enrich failed for %s: %s", brand.primary_domain, exc)

    return BrandResponse(
        id=brand.id, name=brand.name, primary_domain=brand.primary_domain,
        industry=brand.industry, description=brand.description,
        persona=brand.persona, revenue_range=brand.revenue_range,
        logo_path=brand.logo_path, theme_json=brand.theme_json,
        enrichment_status_json=brand.enrichment_status_json,
        created_at=brand.created_at.isoformat() if brand.created_at else None,
        updated_at=brand.updated_at.isoformat() if brand.updated_at else None,
    )


@app.get("/api/brands/{brand_id}", response_model=BrandResponse)
async def get_brand(brand_id: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    audits = db.query(Audit).filter(Audit.brand_id == brand.id).order_by(Audit.created_at.desc()).all()
    latest_score = audits[0].overall_score if audits else None
    previous_score = audits[1].overall_score if len(audits) > 1 else None
    return BrandResponse(
        id=brand.id, name=brand.name, primary_domain=brand.primary_domain,
        industry=brand.industry, description=brand.description,
        persona=brand.persona, revenue_range=brand.revenue_range,
        logo_path=brand.logo_path, theme_json=brand.theme_json,
        enrichment_status_json=brand.enrichment_status_json,
        created_at=brand.created_at.isoformat() if brand.created_at else None,
        updated_at=brand.updated_at.isoformat() if brand.updated_at else None,
        audit_count=len(audits),
        latest_score=latest_score,
        previous_score=previous_score,
    )


@app.patch("/api/brands/{brand_id}", response_model=BrandResponse)
async def update_brand(brand_id: str, req: BrandUpdate, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(brand, key, value)
    brand.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(brand)

    audits = db.query(Audit).filter(Audit.brand_id == brand.id).order_by(Audit.created_at.desc()).all()
    latest_score = audits[0].overall_score if audits else None
    previous_score = audits[1].overall_score if len(audits) > 1 else None

    return BrandResponse(
        id=brand.id, name=brand.name, primary_domain=brand.primary_domain,
        industry=brand.industry, description=brand.description,
        persona=brand.persona, revenue_range=brand.revenue_range,
        logo_path=brand.logo_path, theme_json=brand.theme_json,
        enrichment_status_json=brand.enrichment_status_json,
        created_at=brand.created_at.isoformat() if brand.created_at else None,
        updated_at=brand.updated_at.isoformat() if brand.updated_at else None,
        audit_count=len(audits),
        latest_score=latest_score,
        previous_score=previous_score,
    )


# ============================================================
# Audit history
# ============================================================

@app.get("/api/brands/{brand_id}/audits")
async def list_brand_audits(brand_id: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    audits = db.query(Audit).filter(Audit.brand_id == brand_id).order_by(Audit.created_at.desc()).all()
    results = []
    for i, a in enumerate(audits):
        prev_score = audits[i + 1].overall_score if i + 1 < len(audits) else None
        delta = (a.overall_score - prev_score) if prev_score is not None else None
        results.append(AuditListItem(
            id=a.id, audited_url=a.audited_url, audited_domain=a.audited_domain,
            created_at=a.created_at.isoformat() if a.created_at else None,
            overall_score=a.overall_score, status=a.status,
            error_message=a.error_message, duration_ms=a.duration_ms,
            score_delta=delta,
        ))
    return results


@app.get("/api/audits/{audit_id}", response_model=AuditDetail)
async def get_audit(audit_id: str, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return AuditDetail(
        id=audit.id, brand_id=audit.brand_id,
        audited_url=audit.audited_url, audited_domain=audit.audited_domain,
        created_at=audit.created_at.isoformat() if audit.created_at else None,
        overall_score=audit.overall_score, status=audit.status,
        error_message=audit.error_message, duration_ms=audit.duration_ms,
        category_results_json=audit.category_results_json,
        insights_json=audit.insights_json,
        summary_json=audit.summary_json,
    )


@app.post("/api/brands/{brand_id}/audits")
async def run_brand_audit(brand_id: str, req: AuditRequest, db: Session = Depends(get_db)):
    """Convenience: run audit + save for a brand in one call."""
    req.brand_id = brand_id
    req.save_result = True
    return await run_audit(req, db)


# ============================================================
# File uploads (logo / background image)
# ============================================================

@app.post("/api/uploads")
async def upload_file(
    file: UploadFile = File(...),
    brand_id: Optional[str] = None,
    file_type: str = "logo",  # "logo" or "background"
    db: Session = Depends(get_db),
):
    """Upload a logo or background image. Validates type and size."""
    if file.content_type not in UPLOAD_ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Use PNG, JPEG, SVG, or WebP."
        )

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > UPLOAD_MAX_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Maximum is {UPLOAD_MAX_SIZE_MB}MB."
        )

    # Safe filename: hash + original extension
    ext = os.path.splitext(file.filename or "upload")[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".svg", ".webp"):
        ext = ".png"
    content_hash = hashlib.sha256(contents).hexdigest()[:12]
    safe_name = f"{file_type}_{content_hash}{ext}"

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(UPLOAD_DIR, safe_name)
    with open(filepath, "wb") as f:
        f.write(contents)

    # Attach to brand if specified
    if brand_id:
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if brand:
            if file_type == "logo":
                brand.logo_path = safe_name
            elif file_type == "background":
                theme = brand.theme_json or {}
                theme["bg_image_path"] = safe_name
                brand.theme_json = theme
            brand.updated_at = datetime.now(timezone.utc)
            db.commit()

    return {"filename": safe_name, "size_bytes": len(contents), "type": file_type}


# ============================================================
# Schema Validation — standalone endpoint
# ============================================================

from pydantic import BaseModel as _BaseModel

class SchemaValidateRequest(_BaseModel):
    url: Optional[str] = None
    jsonld: Optional[str] = None

@app.post("/api/schema/validate", response_model=SchemaValidationResult)
async def validate_schema(req: SchemaValidateRequest):
    import json as _json
    from bs4 import BeautifulSoup

    if req.url:
        try:
            page = fetch_page(req.url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not fetch URL: {e}")
        return analyze_schema_validation(page)
    elif req.jsonld:
        try:
            _json.loads(req.jsonld)
        except _json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
        html = f'<html><head><script type="application/ld+json">{req.jsonld}</script></head><body></body></html>'
        from app.fetcher import FetchResult
        import requests as _requests
        resp = _requests.models.Response()
        resp._content = html.encode()
        resp.status_code = 200
        resp.headers["Content-Type"] = "text/html"
        resp.elapsed = __import__("datetime").timedelta(milliseconds=0)
        soup = BeautifulSoup(html, "html.parser")
        page = FetchResult(url="inline://jsonld", response=resp, soup=soup)
        return analyze_schema_validation(page)
    else:
        raise HTTPException(status_code=400, detail="Provide either 'url' or 'jsonld'")


# ============================================================
# Keyword Suggestions — privilege-gated endpoints
# ============================================================

@app.get("/api/keywords/status")
async def keywords_status():
    return {"enabled": FEATURE_KEYWORD_PLANNER_ENABLED}

@app.post("/api/keywords/suggest", response_model=KeywordSuggestResponse)
async def keyword_suggest(
    req: KeywordSuggestRequest,
    x_admin_token: Optional[str] = Header(None),
):
    if not FEATURE_KEYWORD_PLANNER_ENABLED:
        raise HTTPException(status_code=403, detail="Keyword Planner feature is disabled")
    if not KEYWORD_PLANNER_ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Admin token not configured")
    if x_admin_token != KEYWORD_PLANNER_ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")

    return get_keyword_suggestions(
        url=str(req.url),
        seed_keywords=req.seed_keywords,
        language_code=req.language_code,
        geo_target_ids=req.geo_target_ids,
        page_size=req.page_size,
    )
