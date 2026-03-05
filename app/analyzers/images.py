from app.models import CategoryResult, Issue
from app.fetcher import FetchResult


def analyze_images(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    soup = page.soup

    images = soup.find_all("img")
    if not images:
        issues.append(Issue(severity="info", message="No images found on page"))
        return CategoryResult(name="images", score=100, issues=issues,
                              metrics={"total_images": 0, "missing_alt_count": 0, "missing_alt_pct": 0,
                                       "lazy_loading_pct": 0, "missing_dimensions_count": 0})

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

    missing_alt_pct = round(len(missing_alt) / total * 100, 1) if total else 0
    lazy_pct = round(has_lazy / total * 100, 1) if total else 0

    # Alt text
    if missing_alt:
        evidence = ", ".join(missing_alt[:5])
        if len(missing_alt) > 5:
            evidence += f" (+{len(missing_alt) - 5} more)"
        issues.append(Issue(
            severity="error",
            message=f"{len(missing_alt)}/{total} images missing alt attribute ({missing_alt_pct:.0f}%)",
            impact="high",
            recommendation="Add descriptive alt text to all images for accessibility and SEO.",
            evidence=evidence,
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
            message=f"{missing_dimensions}/{total} images missing width/height attributes ({pct:.0f}%)",
            impact="medium",
            recommendation="Add explicit width and height attributes to prevent layout shifts (CLS).",
        ))
        score -= min(20, missing_dimensions * 3)
    else:
        issues.append(Issue(severity="pass", message="All images have explicit dimensions"))

    # Lazy loading
    non_lazy = total - has_lazy
    if total > 3 and non_lazy > 3:
        issues.append(Issue(
            severity="warning",
            message=f"Only {has_lazy}/{total} images use lazy loading",
            impact="medium",
            recommendation="Add loading='lazy' to below-the-fold images to improve page load speed.",
        ))
        score -= 10
    elif has_lazy > 0:
        issues.append(Issue(severity="pass", message=f"{has_lazy}/{total} images use lazy loading"))

    issues.append(Issue(severity="info", message=f"Total images found: {total}"))

    metrics = {
        "total_images": total,
        "missing_alt_count": len(missing_alt),
        "missing_alt_pct": missing_alt_pct,
        "lazy_loading_pct": lazy_pct,
        "missing_dimensions_count": missing_dimensions,
    }

    return CategoryResult(name="images", score=max(0, score), issues=issues, metrics=metrics)
