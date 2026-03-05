from app.models import CategoryResult, Issue
from app.config import MAX_PAGE_SIZE_KB
from app.fetcher import FetchResult


def analyze_performance(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100

    # Response time
    elapsed = page.elapsed_ms
    if elapsed > 3000:
        issues.append(Issue(severity="error", message=f"Very slow response time: {elapsed}ms",
                            impact="high", recommendation="Optimize server response time. Consider caching, CDN, or upgrading hosting.",
                            evidence=f"{elapsed}ms response time"))
        score -= 25
    elif elapsed > 1500:
        issues.append(Issue(severity="warning", message=f"Slow response time: {elapsed}ms",
                            impact="medium", recommendation="Aim for response times under 800ms. Enable server-side caching."))
        score -= 15
    elif elapsed > 800:
        issues.append(Issue(severity="info", message=f"Response time could be better: {elapsed}ms",
                            impact="low", recommendation="Consider optimizing server response for sub-800ms performance."))
        score -= 5
    else:
        issues.append(Issue(severity="pass", message=f"Good response time: {elapsed}ms"))

    # Page size
    size_kb = page.page_size_kb
    if size_kb > MAX_PAGE_SIZE_KB:
        issues.append(Issue(severity="error", message=f"Page size very large: {size_kb:.0f} KB (max {MAX_PAGE_SIZE_KB} KB)",
                            impact="high", recommendation="Reduce page size by compressing images, minifying CSS/JS, and enabling gzip.",
                            evidence=f"{size_kb:.0f} KB"))
        score -= 25
    elif size_kb > 1500:
        issues.append(Issue(severity="warning", message=f"Page size is large: {size_kb:.0f} KB",
                            impact="medium", recommendation="Consider lazy-loading images and deferring non-critical resources."))
        score -= 10
    else:
        issues.append(Issue(severity="pass", message=f"Page size OK: {size_kb:.0f} KB"))

    # HTTPS
    is_https = page.scheme == "https"
    if is_https:
        issues.append(Issue(severity="pass", message="Page served over HTTPS"))
    else:
        issues.append(Issue(severity="error", message="Page not served over HTTPS",
                            impact="high", recommendation="Migrate to HTTPS. It's required for SEO and browser security indicators."))
        score -= 20

    # Render-blocking scripts
    soup = page.soup
    blocking_scripts = soup.find_all("script", attrs={"src": True})
    blocking = [s for s in blocking_scripts if not s.get("async") and not s.get("defer")]
    blocking_count = len(blocking)
    if blocking_count > 3:
        evidence = ", ".join(s.get("src", "")[:60] for s in blocking[:5])
        issues.append(Issue(severity="warning", message=f"{blocking_count} render-blocking scripts found (no async/defer)",
                            impact="medium", recommendation="Add async or defer attributes to non-critical scripts.",
                            evidence=evidence))
        score -= 10
    elif blocking:
        issues.append(Issue(severity="info", message=f"{blocking_count} scripts without async/defer",
                            impact="low", recommendation="Consider adding async or defer to improve page load."))
    else:
        issues.append(Issue(severity="pass", message="All external scripts use async or defer"))

    metrics = {
        "response_time_ms": elapsed,
        "page_size_kb": round(size_kb, 1),
        "is_https": is_https,
        "blocking_scripts_count": blocking_count,
    }

    return CategoryResult(name="performance", score=max(0, score), issues=issues, metrics=metrics)
