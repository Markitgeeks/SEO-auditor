import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

from app.models import (
    AuditRequest, AuditResponse, CategoryResult, IssueSummary,
    CrawlRequest, CrawlResponse, CrawlPageSummary,
    CrawlBrokenLink, CrawlDuplicate,
    PageSpeedResult, SchemaValidationResult,
    KeywordSuggestRequest, KeywordSuggestResponse,
)
from app.external_models import ExternalInsights
from app.report import generate_pdf
from app.fetcher import fetch_page
from app.scoring import compute_overall_score
from app.crawler import crawl_site
from app.utils import normalize_domain, check_ssrf
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
)

import os

app = FastAPI(title="SEO Auditor", version="1.0.0")

# CORS — allow Netlify frontend to call this API
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

# Static file serving — only when running locally (not on Netlify serverless)
_static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

    @app.get("/")
    async def serve_dashboard():
        return FileResponse(os.path.join(_static_dir, "index.html"))


def _run_analyzer(fn, page, name: str) -> CategoryResult:
    start = time.perf_counter()
    try:
        result = fn(page)
        elapsed = int((time.perf_counter() - start) * 1000)
        # Auto-populate summary from issues
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
async def run_audit(req: AuditRequest):
    url = str(req.url)
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

    # Sort to keep consistent order
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

    # --- PageSpeed Insights (opt-in, runs in separate thread) ---
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

    return AuditResponse(
        url=url,
        overall_score=overall,
        categories=categories,
        external_insights=external_insights,
        crawl_results=crawl_results,
        pagespeed_insights=pagespeed_insights,
        schema_validation=schema_validation,
    )


def _run_external_intel(url: str, modules: Optional[list] = None) -> ExternalInsights:
    """Run external intelligence modules in parallel with independent timeouts."""
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
                pass  # Module failures are non-fatal

    return ExternalInsights(similarweb=sw_result, semrush=sr_result)


def _run_crawl(url: str, max_pages: int):
    """Run site crawl and return CrawlResponse, or None on failure."""
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
            url=url,
            pages_crawled=len(result.pages),
            max_depth=result.max_depth,
            pages=pages,
            broken_links=broken_links,
            orphan_pages=result.orphan_pages,
            duplicate_titles=duplicate_titles,
            duplicate_descriptions=duplicate_descriptions,
            score=crawl_analysis.score,
            issues=crawl_analysis.issues,
        )
    except Exception:
        return None


@app.post("/api/crawl", response_model=CrawlResponse)
async def run_crawl(req: CrawlRequest):
    url = str(req.url)
    max_pages = min(req.max_pages, 50)
    result = _run_crawl(url, max_pages)
    if result is None:
        raise HTTPException(status_code=400, detail="Crawl failed")
    return result


@app.post("/api/report/pdf")
async def export_pdf(data: AuditResponse):
    pdf_bytes = generate_pdf(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=seo-audit-report.pdf"},
    )


# ============================================================
# Schema Validation — standalone endpoint
# ============================================================

from pydantic import BaseModel as _BaseModel


class SchemaValidateRequest(_BaseModel):
    url: Optional[str] = None
    jsonld: Optional[str] = None


@app.post("/api/schema/validate", response_model=SchemaValidationResult)
async def validate_schema(req: SchemaValidateRequest):
    """Validate schema markup from a URL or raw JSON-LD snippet."""
    import json as _json
    from bs4 import BeautifulSoup

    if req.url:
        try:
            page = fetch_page(req.url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not fetch URL: {e}")
        return analyze_schema_validation(page)
    elif req.jsonld:
        # Wrap raw JSON-LD in a minimal HTML page for the validator
        try:
            _json.loads(req.jsonld)  # Validate JSON syntax
        except _json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
        html = f'<html><head><script type="application/ld+json">{req.jsonld}</script></head><body></body></html>'
        from app.fetcher import FetchResult
        import requests as _requests
        # Create a minimal FetchResult for the validator
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
    """Check if keyword planner feature is enabled."""
    return {"enabled": FEATURE_KEYWORD_PLANNER_ENABLED}


@app.post("/api/keywords/suggest", response_model=KeywordSuggestResponse)
async def keyword_suggest(
    req: KeywordSuggestRequest,
    x_admin_token: Optional[str] = Header(None),
):
    """Generate keyword suggestions. Requires admin token when enabled."""
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
