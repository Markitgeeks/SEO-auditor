from app.models import CategoryResult, Issue
from app.config import MAX_PAGE_SIZE_KB
from app.fetcher import FetchResult


def analyze_performance(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100

    # Response time
    elapsed = page.elapsed_ms
    if elapsed > 3000:
        issues.append(Issue(severity="error", message=f"Very slow response time: {elapsed}ms"))
        score -= 25
    elif elapsed > 1500:
        issues.append(Issue(severity="warning", message=f"Slow response time: {elapsed}ms"))
        score -= 15
    elif elapsed > 800:
        issues.append(Issue(severity="info", message=f"Response time could be better: {elapsed}ms"))
        score -= 5
    else:
        issues.append(Issue(severity="pass", message=f"Good response time: {elapsed}ms"))

    # Page size
    size_kb = page.page_size_kb
    if size_kb > MAX_PAGE_SIZE_KB:
        issues.append(Issue(severity="error", message=f"Page size very large: {size_kb:.0f} KB (max {MAX_PAGE_SIZE_KB} KB)"))
        score -= 25
    elif size_kb > 1500:
        issues.append(Issue(severity="warning", message=f"Page size is large: {size_kb:.0f} KB"))
        score -= 10
    else:
        issues.append(Issue(severity="pass", message=f"Page size OK: {size_kb:.0f} KB"))

    # HTTPS
    if page.scheme == "https":
        issues.append(Issue(severity="pass", message="Page served over HTTPS"))
    else:
        issues.append(Issue(severity="error", message="Page not served over HTTPS"))
        score -= 20

    # Render-blocking scripts
    soup = page.soup
    blocking_scripts = soup.find_all("script", attrs={"src": True})
    blocking = [s for s in blocking_scripts if not s.get("async") and not s.get("defer")]
    if len(blocking) > 3:
        issues.append(Issue(severity="warning", message=f"{len(blocking)} render-blocking scripts found (no async/defer)"))
        score -= 10
    elif blocking:
        issues.append(Issue(severity="info", message=f"{len(blocking)} scripts without async/defer"))
    else:
        issues.append(Issue(severity="pass", message="All external scripts use async or defer"))

    return CategoryResult(name="performance", score=max(0, score), issues=issues)
