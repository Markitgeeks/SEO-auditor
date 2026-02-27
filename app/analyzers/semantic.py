import re
from app.models import CategoryResult, Issue
from app.fetcher import FetchResult


def analyze_semantic(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    soup = page.soup

    # --- HTML5 semantic elements ---
    semantic_tags = {
        "header": soup.find_all("header"),
        "nav": soup.find_all("nav"),
        "main": soup.find_all("main"),
        "article": soup.find_all("article"),
        "section": soup.find_all("section"),
        "aside": soup.find_all("aside"),
        "footer": soup.find_all("footer"),
    }

    found = [tag for tag, els in semantic_tags.items() if els]
    if found:
        issues.append(Issue(severity="pass", message=f"Semantic elements found: {', '.join(found)}"))
    else:
        issues.append(Issue(severity="error", message="No HTML5 semantic elements found"))

    # Single <main> required
    main_count = len(semantic_tags["main"])
    if main_count == 0:
        issues.append(Issue(severity="error", message="Missing <main> element"))
        score -= 20
    elif main_count == 1:
        issues.append(Issue(severity="pass", message="Single <main> element present"))
    else:
        issues.append(Issue(severity="warning", message=f"Multiple <main> elements found ({main_count}); should be exactly 1"))
        score -= 10

    # <nav> presence
    if not semantic_tags["nav"]:
        issues.append(Issue(severity="warning", message="No <nav> element found"))
        score -= 15
    else:
        issues.append(Issue(severity="pass", message=f"{len(semantic_tags['nav'])} <nav> element(s) found"))

    # header / footer
    if not semantic_tags["header"]:
        issues.append(Issue(severity="warning", message="No <header> element found"))
        score -= 10
    if not semantic_tags["footer"]:
        issues.append(Issue(severity="warning", message="No <footer> element found"))
        score -= 10

    # --- ARIA landmark roles ---
    aria_roles = ["banner", "navigation", "main", "contentinfo"]
    found_roles = []
    for role in aria_roles:
        if soup.find(attrs={"role": role}):
            found_roles.append(role)
    if found_roles:
        issues.append(Issue(severity="pass", message=f"ARIA landmark roles found: {', '.join(found_roles)}"))
    else:
        issues.append(Issue(severity="info", message="No ARIA landmark roles detected"))

    # --- Content-to-HTML ratio ---
    body = soup.find("body")
    if body:
        text = body.get_text(separator=" ", strip=True)
        total_html = len(page.response.text)
        text_len = len(text)
        if total_html > 0:
            ratio = (text_len / total_html) * 100
            if ratio >= 25:
                issues.append(Issue(severity="pass", message=f"Content-to-HTML ratio: {ratio:.1f}%"))
            elif ratio >= 10:
                issues.append(Issue(severity="info", message=f"Content-to-HTML ratio: {ratio:.1f}% (moderate)"))
            else:
                issues.append(Issue(severity="warning", message=f"Content-to-HTML ratio: {ratio:.1f}% (low — heavy markup)"))
                score -= 15

    # --- Lists for structured content ---
    ul_count = len(soup.find_all("ul"))
    ol_count = len(soup.find_all("ol"))
    if ul_count or ol_count:
        issues.append(Issue(severity="info", message=f"Lists found: {ul_count} <ul>, {ol_count} <ol>"))
    else:
        issues.append(Issue(severity="info", message="No list elements (<ul>/<ol>) found"))

    # --- <figure> + <figcaption> ---
    figures = soup.find_all("figure")
    if figures:
        with_caption = sum(1 for f in figures if f.find("figcaption"))
        issues.append(Issue(severity="info", message=f"{len(figures)} <figure> element(s), {with_caption} with <figcaption>"))

    # --- <time datetime=""> ---
    times = soup.find_all("time")
    if times:
        with_dt = sum(1 for t in times if t.get("datetime"))
        issues.append(Issue(severity="info", message=f"{len(times)} <time> element(s), {with_dt} with datetime attribute"))

    return CategoryResult(name="semantic", score=max(0, score), issues=issues)
