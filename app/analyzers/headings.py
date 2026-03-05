from app.models import CategoryResult, Issue
from app.config import H1_MAX_LENGTH
from app.fetcher import FetchResult


def analyze_headings(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    soup = page.soup

    h1s = soup.find_all("h1")
    h1_count = len(h1s)
    h1_text = ""

    if h1_count == 0:
        issues.append(Issue(severity="error", message="No H1 tag found",
                            impact="high", recommendation="Add a single, descriptive H1 tag that includes your primary keyword."))
        score -= 30
    elif h1_count > 1:
        h1_text = h1s[0].get_text(strip=True)
        texts = [h.get_text(strip=True)[:50] for h in h1s]
        issues.append(Issue(severity="warning", message=f"Multiple H1 tags found ({h1_count})",
                            impact="medium", recommendation="Use only one H1 per page for clear topic signaling.",
                            evidence="; ".join(texts)))
        score -= 15
    else:
        h1_text = h1s[0].get_text(strip=True)
        if len(h1_text) > H1_MAX_LENGTH:
            issues.append(Issue(severity="warning", message=f"H1 too long ({len(h1_text)} chars, max {H1_MAX_LENGTH})",
                                impact="low", recommendation=f"Shorten H1 to under {H1_MAX_LENGTH} characters.",
                                evidence=h1_text[:80]))
            score -= 10
        elif not h1_text:
            issues.append(Issue(severity="error", message="H1 tag is empty",
                                impact="high", recommendation="Add descriptive text to the H1 tag."))
            score -= 20
        else:
            issues.append(Issue(severity="pass", message=f"Single H1 found: \"{h1_text[:60]}\""))

    # Check heading hierarchy
    seen_levels = []
    for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        if soup.find(tag_name):
            seen_levels.append(int(tag_name[1]))

    hierarchy_valid = True
    for i in range(1, len(seen_levels)):
        if seen_levels[i] - seen_levels[i - 1] > 1:
            hierarchy_valid = False
            issues.append(Issue(
                severity="warning",
                message=f"Heading hierarchy skips from H{seen_levels[i-1]} to H{seen_levels[i]}",
                impact="medium",
                recommendation="Use sequential heading levels (H1 → H2 → H3) without skipping."
            ))
            score -= 10

    if hierarchy_valid and len(seen_levels) > 1:
        issues.append(Issue(severity="pass", message="Heading hierarchy is sequential"))

    # Count headings
    heading_counts = {}
    total = 0
    for i in range(1, 7):
        count = len(soup.find_all(f"h{i}"))
        if count:
            heading_counts[f"h{i}"] = count
        total += count

    if total == 0:
        issues.append(Issue(severity="error", message="No heading tags found on page",
                            impact="high", recommendation="Add heading tags to structure your content for SEO and accessibility."))
        score -= 20
    else:
        breakdown = ", ".join(f"H{i}: {len(soup.find_all(f'h{i}'))}" for i in range(1, 7) if soup.find_all(f"h{i}"))
        issues.append(Issue(severity="info", message=f"Heading counts — {breakdown}"))

    metrics = {
        "h1_count": h1_count,
        "h1_text": h1_text[:80] if h1_text else None,
        "total_headings": total,
        "hierarchy_valid": hierarchy_valid,
        "heading_counts": heading_counts,
    }

    return CategoryResult(name="headings", score=max(0, score), issues=issues, metrics=metrics)
