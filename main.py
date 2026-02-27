from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.models import AuditRequest, AuditResponse, CategoryResult
from app.fetcher import fetch_page
from app.scoring import compute_overall_score
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
