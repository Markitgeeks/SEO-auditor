from urllib.parse import urlparse

from app.models import CategoryResult, Issue
from app.fetcher import FetchResult


def analyze_links(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    soup = page.soup
    domain = page.domain

    anchors = soup.find_all("a")
    internal = 0
    external = 0
    empty_href = 0
    nofollow_internal = 0

    for a in anchors:
        href = a.get("href", "").strip()
        if not href or href == "#" or href.startswith("javascript:"):
            empty_href += 1
            continue

        rel = a.get("rel", [])
        if isinstance(rel, str):
            rel = rel.split()

        parsed = urlparse(href)
        if parsed.netloc and parsed.netloc != domain:
            external += 1
        else:
            internal += 1
            if "nofollow" in rel:
                nofollow_internal += 1

    total = len(anchors)
    issues.append(Issue(severity="info", message=f"Total links: {total} (internal: {internal}, external: {external})"))

    if empty_href:
        issues.append(Issue(severity="warning", message=f"{empty_href} links have empty or invalid href"))
        score -= min(15, empty_href * 3)
    else:
        issues.append(Issue(severity="pass", message="No empty or invalid hrefs found"))

    if nofollow_internal:
        issues.append(Issue(severity="warning", message=f"{nofollow_internal} internal links have rel=\"nofollow\""))
        score -= min(15, nofollow_internal * 5)
    else:
        issues.append(Issue(severity="pass", message="No internal links with nofollow"))

    if internal == 0 and total > 0:
        issues.append(Issue(severity="error", message="No internal links found"))
        score -= 20
    elif internal > 0:
        issues.append(Issue(severity="pass", message=f"{internal} internal links found"))

    if external == 0 and total > 5:
        issues.append(Issue(severity="info", message="No external links found — consider linking to authoritative sources"))

    return CategoryResult(name="links", score=max(0, score), issues=issues)
