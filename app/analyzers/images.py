from app.models import CategoryResult, Issue
from app.fetcher import FetchResult


def analyze_images(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    soup = page.soup

    images = soup.find_all("img")
    if not images:
        issues.append(Issue(severity="info", message="No images found on page"))
        return CategoryResult(name="images", score=100, issues=issues)

    total = len(images)
    missing_alt = []
    empty_alt = 0
    missing_dimensions = 0
    has_lazy = 0

    for img in images:
        src = img.get("src", img.get("data-src", ""))[:80]
        alt = img.get("alt")
        if alt is None:
            missing_alt.append(src or "(no src)")
        elif alt.strip() == "":
            empty_alt += 1

        if not img.get("width") or not img.get("height"):
            missing_dimensions += 1

        if img.get("loading") == "lazy":
            has_lazy += 1

    # Alt text
    if missing_alt:
        pct = len(missing_alt) / total * 100
        issues.append(Issue(
            severity="error",
            message=f"{len(missing_alt)}/{total} images missing alt attribute ({pct:.0f}%)"
        ))
        score -= min(40, len(missing_alt) * 5)
    else:
        issues.append(Issue(severity="pass", message="All images have alt attributes"))

    if empty_alt:
        issues.append(Issue(severity="info", message=f"{empty_alt} images have empty alt (decorative)"))

    # Dimensions
    if missing_dimensions:
        pct = missing_dimensions / total * 100
        issues.append(Issue(
            severity="warning",
            message=f"{missing_dimensions}/{total} images missing width/height attributes ({pct:.0f}%)"
        ))
        score -= min(20, missing_dimensions * 3)
    else:
        issues.append(Issue(severity="pass", message="All images have explicit dimensions"))

    # Lazy loading
    non_lazy = total - has_lazy
    if total > 3 and non_lazy > 3:
        issues.append(Issue(
            severity="warning",
            message=f"Only {has_lazy}/{total} images use lazy loading"
        ))
        score -= 10
    elif has_lazy > 0:
        issues.append(Issue(severity="pass", message=f"{has_lazy}/{total} images use lazy loading"))

    issues.append(Issue(severity="info", message=f"Total images found: {total}"))

    return CategoryResult(name="images", score=max(0, score), issues=issues)
