from app.models import CategoryResult, Issue
from app.config import H1_MAX_LENGTH
from app.fetcher import FetchResult


def analyze_headings(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    soup = page.soup

    h1s = soup.find_all("h1")
    if len(h1s) == 0:
        issues.append(Issue(severity="error", message="No H1 tag found"))
        score -= 30
    elif len(h1s) > 1:
        issues.append(Issue(severity="warning", message=f"Multiple H1 tags found ({len(h1s)})"))
        score -= 15
    else:
        h1_text = h1s[0].get_text(strip=True)
        if len(h1_text) > H1_MAX_LENGTH:
            issues.append(Issue(severity="warning", message=f"H1 too long ({len(h1_text)} chars, max {H1_MAX_LENGTH})"))
            score -= 10
        elif not h1_text:
            issues.append(Issue(severity="error", message="H1 tag is empty"))
            score -= 20
        else:
            issues.append(Issue(severity="pass", message=f"Single H1 found: \"{h1_text[:60]}\""))

    # Check heading hierarchy
    headings = []
    for level in range(1, 7):
        for tag in soup.find_all(f"h{level}"):
            headings.append(level)

    # Detect skipped levels by checking order of first appearances
    seen_levels = []
    for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        if soup.find(tag_name):
            seen_levels.append(int(tag_name[1]))

    skipped = False
    for i in range(1, len(seen_levels)):
        if seen_levels[i] - seen_levels[i - 1] > 1:
            skipped = True
            issues.append(Issue(
                severity="warning",
                message=f"Heading hierarchy skips from H{seen_levels[i-1]} to H{seen_levels[i]}"
            ))
            score -= 10

    if not skipped and len(seen_levels) > 1:
        issues.append(Issue(severity="pass", message="Heading hierarchy is sequential"))

    # Count headings
    total = sum(len(soup.find_all(f"h{i}")) for i in range(1, 7))
    if total == 0:
        issues.append(Issue(severity="error", message="No heading tags found on page"))
        score -= 20
    else:
        breakdown = ", ".join(
            f"H{i}: {len(soup.find_all(f'h{i}'))}"
            for i in range(1, 7)
            if soup.find_all(f"h{i}")
        )
        issues.append(Issue(severity="info", message=f"Heading counts — {breakdown}"))

    return CategoryResult(name="headings", score=max(0, score), issues=issues)
