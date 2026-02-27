from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

from app.models import (
    AuditRequest, AuditResponse, CategoryResult,
    CrawlRequest, CrawlResponse, CrawlPageSummary,
    CrawlBrokenLink, CrawlDuplicate,
)
from app.report import generate_pdf
from app.fetcher import fetch_page
from app.scoring import compute_overall_score
from app.crawler import crawl_site
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
)

app = FastAPI(title="SEO Auditor", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_dashboard():
    return FileResponse("static/index.html")


def _run_analyzer(fn, page, name: str) -> CategoryResult:
    try:
        return fn(page)
    except Exception:
        return CategoryResult(name=name, score=0, issues=[])


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

    return AuditResponse(url=url, overall_score=overall, categories=categories)


@app.post("/api/crawl", response_model=CrawlResponse)
async def run_crawl(req: CrawlRequest):
    url = str(req.url)
    max_pages = min(req.max_pages, 50)  # hard cap

    try:
        result = crawl_site(url, max_pages=max_pages)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Crawl failed: {e}")

    # Analyze crawl results
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


@app.post("/api/report/pdf")
async def export_pdf(data: AuditResponse):
    pdf_bytes = generate_pdf(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=seo-audit-report.pdf"},
    )
