from app.models import CategoryResult, Issue
from app.fetcher import FetchResult


def analyze_mobile(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    soup = page.soup

    # Viewport meta
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if not viewport:
        issues.append(Issue(severity="error", message="Missing viewport meta tag"))
        score -= 40
    else:
        content = viewport.get("content", "")
        issues.append(Issue(severity="pass", message=f"Viewport meta tag found: {content[:80]}"))

        if "width=device-width" not in content:
            issues.append(Issue(severity="warning", message="Viewport missing width=device-width"))
            score -= 15

        if "user-scalable=no" in content or "maximum-scale=1" in content:
            issues.append(Issue(severity="warning", message="Viewport disables user zooming — poor accessibility"))
            score -= 15
        else:
            issues.append(Issue(severity="pass", message="User zooming is allowed"))

    # Fixed-width heuristics: look for inline styles with fixed pixel widths
    fixed_width_elements = 0
    for tag in soup.find_all(style=True):
        style = tag.get("style", "")
        if "width:" in style and "px" in style:
            # Simple heuristic: check for large fixed widths
            parts = style.split("width:")
            for part in parts[1:]:
                val = part.strip().split("px")[0].strip().rstrip(";").strip()
                try:
                    if float(val) > 500:
                        fixed_width_elements += 1
                except ValueError:
                    pass

    if fixed_width_elements:
        issues.append(Issue(severity="warning", message=f"{fixed_width_elements} elements with large fixed pixel widths detected"))
        score -= min(20, fixed_width_elements * 5)
    else:
        issues.append(Issue(severity="pass", message="No large fixed-width elements detected"))

    # Check for media queries in inline styles (basic check)
    style_tags = soup.find_all("style")
    has_responsive = any("@media" in (s.string or "") for s in style_tags)
    link_tags = soup.find_all("link", attrs={"rel": "stylesheet", "media": True})
    has_responsive = has_responsive or bool(link_tags)
    if has_responsive:
        issues.append(Issue(severity="pass", message="Responsive CSS detected (media queries)"))
    else:
        issues.append(Issue(severity="info", message="No inline responsive CSS detected (may use external stylesheets)"))

    return CategoryResult(name="mobile", score=max(0, score), issues=issues)
