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
    semantic_elements = len(found)
    if found:
        issues.append(Issue(severity="pass", message=f"Semantic elements found: {', '.join(found)}"))
    else:
        issues.append(Issue(severity="error", message="No HTML5 semantic elements found",
                            impact="high", recommendation="Use semantic HTML5 elements (header, nav, main, article, section, footer) for better SEO and accessibility."))

    # Single <main> required
    main_count = len(semantic_tags["main"])
    if main_count == 0:
        issues.append(Issue(severity="error", message="Missing <main> element",
                            impact="high", recommendation="Add a single <main> element to wrap your primary content."))
        score -= 20
    elif main_count == 1:
        issues.append(Issue(severity="pass", message="Single <main> element present"))
    else:
        issues.append(Issue(severity="warning", message=f"Multiple <main> elements found ({main_count}); should be exactly 1",
                            impact="medium", recommendation="Use only one <main> element per page."))
        score -= 10

    # <nav> presence
    if not semantic_tags["nav"]:
        issues.append(Issue(severity="warning", message="No <nav> element found",
                            impact="medium", recommendation="Wrap your navigation in a <nav> element for accessibility."))
        score -= 15
    else:
        issues.append(Issue(severity="pass", message=f"{len(semantic_tags['nav'])} <nav> element(s) found"))

    # header / footer
    if not semantic_tags["header"]:
        issues.append(Issue(severity="warning", message="No <header> element found",
                            impact="low", recommendation="Add a <header> element for your page or site header."))
        score -= 10
    if not semantic_tags["footer"]:
        issues.append(Issue(severity="warning", message="No <footer> element found",
                            impact="low", recommendation="Add a <footer> element for your page footer."))
        score -= 10

    # --- ARIA landmark roles ---
    aria_role_list = ["banner", "navigation", "main", "contentinfo"]
    found_roles = []
    for role in aria_role_list:
        if soup.find(attrs={"role": role}):
            found_roles.append(role)
    aria_roles = len(found_roles)
    if found_roles:
        issues.append(Issue(severity="pass", message=f"ARIA landmark roles found: {', '.join(found_roles)}"))
    else:
        issues.append(Issue(severity="info", message="No ARIA landmark roles detected",
                            impact="low", recommendation="Consider adding ARIA roles for enhanced screen reader navigation."))

    # --- Content-to-HTML ratio ---
    content_to_html_ratio = 0.0
    body = soup.find("body")
    if body:
        text = body.get_text(separator=" ", strip=True)
        total_html = len(page.response.text)
        text_len = len(text)
        if total_html > 0:
            content_to_html_ratio = round((text_len / total_html) * 100, 1)
            if content_to_html_ratio >= 25:
                issues.append(Issue(severity="pass", message=f"Content-to-HTML ratio: {content_to_html_ratio}%"))
            elif content_to_html_ratio >= 10:
                issues.append(Issue(severity="info", message=f"Content-to-HTML ratio: {content_to_html_ratio}% (moderate)"))
            else:
                issues.append(Issue(severity="warning", message=f"Content-to-HTML ratio: {content_to_html_ratio}% (low — heavy markup)",
                                    impact="medium", recommendation="Reduce unnecessary markup and inline styles to improve content ratio."))
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

    metrics = {
        "semantic_elements": semantic_elements,
        "aria_roles": aria_roles,
        "content_to_html_ratio": content_to_html_ratio,
        "main_count": main_count,
    }

    return CategoryResult(name="semantic", score=max(0, score), issues=issues, metrics=metrics)
