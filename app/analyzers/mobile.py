from app.models import CategoryResult, Issue
from app.fetcher import FetchResult


def analyze_mobile(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    soup = page.soup

    # Viewport meta
    viewport = soup.find("meta", attrs={"name": "viewport"})
    has_viewport = viewport is not None
    zoom_disabled = False

    if not has_viewport:
        issues.append(Issue(severity="error", message="Missing viewport meta tag",
                            impact="high", recommendation="Add <meta name='viewport' content='width=device-width, initial-scale=1'>"))
        score -= 40
    else:
        content = viewport.get("content", "")
        issues.append(Issue(severity="pass", message=f"Viewport meta tag found: {content[:80]}"))

        if "width=device-width" not in content:
            issues.append(Issue(severity="warning", message="Viewport missing width=device-width",
                                impact="medium", recommendation="Add width=device-width to the viewport meta tag for proper mobile rendering."))
            score -= 15

        if "user-scalable=no" in content or "maximum-scale=1" in content:
            zoom_disabled = True
            issues.append(Issue(severity="warning", message="Viewport disables user zooming — poor accessibility",
                                impact="medium", recommendation="Remove user-scalable=no and maximum-scale=1 to allow pinch-to-zoom."))
            score -= 15
        else:
            issues.append(Issue(severity="pass", message="User zooming is allowed"))

    # Fixed-width heuristics
    fixed_width_elements = 0
    for tag in soup.find_all(style=True):
        style = tag.get("style", "")
        if "width:" in style and "px" in style:
            parts = style.split("width:")
            for part in parts[1:]:
                val = part.strip().split("px")[0].strip().rstrip(";").strip()
                try:
                    if float(val) > 500:
                        fixed_width_elements += 1
                except ValueError:
                    pass

    if fixed_width_elements:
        issues.append(Issue(severity="warning", message=f"{fixed_width_elements} elements with large fixed pixel widths detected",
                            impact="medium", recommendation="Replace fixed pixel widths with responsive units (%, vw, max-width)."))
        score -= min(20, fixed_width_elements * 5)
    else:
        issues.append(Issue(severity="pass", message="No large fixed-width elements detected"))

    # Check for media queries
    style_tags = soup.find_all("style")
    has_media_queries = any("@media" in (s.string or "") for s in style_tags)
    link_tags = soup.find_all("link", attrs={"rel": "stylesheet", "media": True})
    has_media_queries = has_media_queries or bool(link_tags)
    if has_media_queries:
        issues.append(Issue(severity="pass", message="Responsive CSS detected (media queries)"))
    else:
        issues.append(Issue(severity="info", message="No inline responsive CSS detected (may use external stylesheets)",
                            impact="low", recommendation="Ensure your external stylesheets include responsive breakpoints."))

    metrics = {
        "has_viewport": has_viewport,
        "zoom_disabled": zoom_disabled,
        "fixed_width_elements": fixed_width_elements,
        "has_media_queries": has_media_queries,
    }

    return CategoryResult(name="mobile", score=max(0, score), issues=issues, metrics=metrics)
