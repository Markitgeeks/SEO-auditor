from app.models import CategoryResult, Issue
from app.config import TITLE_MIN_LENGTH, TITLE_MAX_LENGTH, DESCRIPTION_MIN_LENGTH, DESCRIPTION_MAX_LENGTH
from app.fetcher import FetchResult


def analyze_meta_tags(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    soup = page.soup

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    if not title:
        issues.append(Issue(severity="error", message="Missing <title> tag",
                            impact="high", recommendation=f"Add a unique <title> of {TITLE_MIN_LENGTH}-{TITLE_MAX_LENGTH} characters."))
        score -= 25
    elif len(title) < TITLE_MIN_LENGTH:
        issues.append(Issue(severity="warning", message=f"Title too short ({len(title)} chars, recommended {TITLE_MIN_LENGTH}-{TITLE_MAX_LENGTH})",
                            impact="medium", recommendation=f"Expand the title to at least {TITLE_MIN_LENGTH} characters with relevant keywords.",
                            evidence=title))
        score -= 10
    elif len(title) > TITLE_MAX_LENGTH:
        issues.append(Issue(severity="warning", message=f"Title too long ({len(title)} chars, recommended {TITLE_MIN_LENGTH}-{TITLE_MAX_LENGTH})",
                            impact="medium", recommendation=f"Shorten the title to under {TITLE_MAX_LENGTH} characters to avoid truncation in SERPs.",
                            evidence=title))
        score -= 10
    else:
        issues.append(Issue(severity="pass", message=f"Title length is good ({len(title)} chars)"))

    # Meta description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc = desc_tag.get("content", "").strip() if desc_tag else ""
    if not desc:
        issues.append(Issue(severity="error", message="Missing meta description",
                            impact="high", recommendation=f"Add a meta description of {DESCRIPTION_MIN_LENGTH}-{DESCRIPTION_MAX_LENGTH} characters."))
        score -= 20
    elif len(desc) < DESCRIPTION_MIN_LENGTH:
        issues.append(Issue(severity="warning", message=f"Meta description too short ({len(desc)} chars, recommended {DESCRIPTION_MIN_LENGTH}-{DESCRIPTION_MAX_LENGTH})",
                            impact="medium", recommendation=f"Expand to at least {DESCRIPTION_MIN_LENGTH} characters for better click-through rates.",
                            evidence=desc[:120]))
        score -= 10
    elif len(desc) > DESCRIPTION_MAX_LENGTH:
        issues.append(Issue(severity="warning", message=f"Meta description too long ({len(desc)} chars, recommended {DESCRIPTION_MIN_LENGTH}-{DESCRIPTION_MAX_LENGTH})",
                            impact="low", recommendation="Shorten to avoid truncation in search results.",
                            evidence=desc[:120]))
        score -= 5
    else:
        issues.append(Issue(severity="pass", message=f"Meta description length is good ({len(desc)} chars)"))

    # Canonical
    canonical = soup.find("link", attrs={"rel": "canonical"})
    has_canonical = canonical is not None
    if not has_canonical:
        issues.append(Issue(severity="warning", message="Missing canonical URL",
                            impact="medium", recommendation="Add a <link rel='canonical'> to prevent duplicate content issues."))
        score -= 10
    else:
        issues.append(Issue(severity="pass", message=f"Canonical URL found: {canonical.get('href', '')}"))

    # Open Graph
    og_tags = soup.find_all("meta", attrs={"property": lambda v: v and v.startswith("og:")})
    required_og = {"og:title", "og:description", "og:image", "og:url"}
    found_og = {tag.get("property") for tag in og_tags}
    missing_og = required_og - found_og
    og_count = len(og_tags)
    if missing_og:
        issues.append(Issue(severity="warning", message=f"Missing Open Graph tags: {', '.join(sorted(missing_og))}",
                            impact="medium", recommendation="Add missing OG tags for better social media sharing previews.",
                            evidence=f"Missing: {', '.join(sorted(missing_og))}"))
        score -= min(15, len(missing_og) * 4)
    else:
        issues.append(Issue(severity="pass", message="All essential Open Graph tags present"))

    # Twitter cards
    twitter_tags = soup.find_all("meta", attrs={"name": lambda v: v and v.startswith("twitter:")})
    if not twitter_tags:
        issues.append(Issue(severity="info", message="No Twitter Card meta tags found",
                            impact="low", recommendation="Add Twitter Card tags for optimized Twitter/X sharing."))
        score -= 5
    else:
        issues.append(Issue(severity="pass", message=f"Twitter Card tags found ({len(twitter_tags)})"))

    # Lang attribute
    html_tag = soup.find("html")
    has_lang = bool(html_tag and html_tag.get("lang"))
    if has_lang:
        issues.append(Issue(severity="pass", message=f"Language attribute set: {html_tag.get('lang')}"))
    else:
        issues.append(Issue(severity="warning", message="Missing lang attribute on <html> tag",
                            impact="medium", recommendation="Add lang attribute (e.g., lang='en') for accessibility and SEO."))
        score -= 5

    metrics = {
        "title_length": len(title),
        "description_length": len(desc),
        "has_canonical": has_canonical,
        "og_tags_count": og_count,
        "has_lang": has_lang,
    }

    return CategoryResult(name="meta_tags", score=max(0, score), issues=issues, metrics=metrics)
