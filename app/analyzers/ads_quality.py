"""Google Ads landing page quality scoring."""

from __future__ import annotations

import re

from app.models import CategoryResult, Issue
from app.fetcher import FetchResult


def _check_https(page: FetchResult, issues: list[Issue]) -> int:
    if page.scheme == "https":
        issues.append(Issue(severity="pass", message="Page served over HTTPS"))
        return 0
    issues.append(Issue(severity="error", message="Page not served over HTTPS -- required for Google Ads",
                        impact="high", recommendation="Migrate to HTTPS. Google Ads requires secure landing pages."))
    return -15


def _check_load_speed(page: FetchResult, issues: list[Issue]) -> int:
    ms = page.elapsed_ms
    if ms < 1000:
        issues.append(Issue(severity="pass", message=f"Fast page load ({ms}ms)"))
        return 0
    if ms < 3000:
        issues.append(Issue(severity="warning", message=f"Moderate page load ({ms}ms) -- aim for under 1s",
                            impact="medium", recommendation="Optimize page load time to under 1 second for better ad quality scores."))
        return -5
    issues.append(Issue(severity="error", message=f"Slow page load ({ms}ms) -- Google Ads penalizes slow pages",
                        impact="high", recommendation="Significantly improve page speed. Consider CDN, image compression, and code splitting."))
    return -15


def _check_mobile_viewport(page: FetchResult, issues: list[Issue]) -> int:
    viewport = page.soup.find("meta", attrs={"name": "viewport"})
    if viewport:
        issues.append(Issue(severity="pass", message="Mobile viewport meta tag present"))
        return 0
    issues.append(Issue(severity="error", message="Missing viewport meta tag -- critical for mobile Ads traffic",
                        impact="high", recommendation="Add <meta name='viewport' content='width=device-width, initial-scale=1'>"))
    return -15


def _check_content_relevance(page: FetchResult, issues: list[Issue]) -> tuple[int, int]:
    penalty = 0
    body = page.soup.find("body")
    text = body.get_text(separator=" ", strip=True) if body else ""
    word_count = len(text.split())

    if word_count < 100:
        issues.append(Issue(severity="warning", message=f"Thin content ({word_count} words) -- Google Ads prefers substantive pages",
                            impact="medium", recommendation="Add more relevant content to improve ad quality score and user experience."))
        penalty -= 10
    elif word_count < 300:
        issues.append(Issue(severity="info", message=f"Content has {word_count} words -- consider adding more for quality score",
                            impact="low", recommendation="Expanding content beyond 300 words can improve ad landing page quality."))
        penalty -= 3
    else:
        issues.append(Issue(severity="pass", message=f"Good content depth ({word_count} words)"))

    title = page.soup.find("title")
    h1 = page.soup.find("h1")
    if title and h1:
        issues.append(Issue(severity="pass", message="Title and H1 both present for keyword relevance"))
    elif not title:
        issues.append(Issue(severity="warning", message="Missing title tag -- hurts ad relevance score",
                            impact="medium", recommendation="Add a <title> tag with relevant keywords."))
        penalty -= 5
    elif not h1:
        issues.append(Issue(severity="info", message="No H1 tag -- consider adding for ad landing page relevance",
                            impact="low", recommendation="Add an H1 heading that matches your ad copy keywords."))
        penalty -= 2

    return penalty, word_count


def _check_conversion_tracking(page: FetchResult, issues: list[Issue]) -> tuple[int, list[str]]:
    html = page.response.text
    trackers_found = []

    patterns = {
        "Google Analytics (GA4)": r"gtag\(|googletagmanager\.com|google-analytics\.com|GA1\.",
        "Google Tag Manager": r"gtm\.js|GTM-[A-Z0-9]+",
        "Google Ads Conversion": r"googleads\.g\.doubleclick\.net|AW-[0-9]+|conversion\.js",
        "Facebook Pixel": r"fbq\(|connect\.facebook\.net/.*fbevents",
    }

    for name, pattern in patterns.items():
        if re.search(pattern, html, re.IGNORECASE):
            trackers_found.append(name)

    if trackers_found:
        issues.append(Issue(severity="pass", message=f"Conversion tracking detected: {', '.join(trackers_found)}"))
        return 0, trackers_found
    issues.append(Issue(severity="warning", message="No conversion tracking detected -- add Google Ads conversion pixel or GA4",
                        impact="medium", recommendation="Install Google Ads conversion tracking to measure campaign ROI."))
    return -10, trackers_found


def _check_cta_and_forms(page: FetchResult, issues: list[Issue]) -> tuple[int, int]:
    penalty = 0
    soup = page.soup
    cta_count = 0

    cta_pattern = re.compile(
        r"\b(buy\s*now|add\s*to\s*cart|shop\s*now|sign\s*up|get\s*started|subscribe|"
        r"learn\s*more|contact\s*us|request\s*a?\s*quote|book\s*now|order\s*now|"
        r"free\s*trial|download|register)\b",
        re.IGNORECASE,
    )
    cta_elements = soup.find_all(["a", "button"], string=cta_pattern)
    cta_inputs = soup.find_all("input", attrs={"value": cta_pattern})
    cta_count = len(cta_elements) + len(cta_inputs)

    if cta_count:
        issues.append(Issue(severity="pass", message=f"{cta_count} call-to-action element(s) detected"))
    else:
        issues.append(Issue(severity="warning", message="No clear CTA found (buy now, sign up, etc.)",
                            impact="medium", recommendation="Add a clear call-to-action button matching your ad copy."))
        penalty -= 5

    forms = soup.find_all("form")
    if forms:
        labels = soup.find_all("label")
        submits = soup.find_all(["button", "input"], attrs={"type": re.compile(r"submit", re.I)})
        if labels and submits:
            issues.append(Issue(severity="pass", message=f"{len(forms)} form(s) with labels and submit buttons"))
        elif forms:
            issues.append(Issue(severity="info", message=f"{len(forms)} form(s) found -- ensure labels and submit buttons are present"))

    return penalty, cta_count


def _check_ad_schema(page: FetchResult, issues: list[Issue]) -> int:
    import json
    for script in page.soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                schema_type = item.get("@type", "")
                if isinstance(schema_type, list):
                    schema_type = schema_type[0] if schema_type else ""
                if schema_type in ("Product", "LocalBusiness", "Service"):
                    if "offers" in item or "priceRange" in item:
                        issues.append(Issue(severity="pass", message=f"{schema_type} schema with pricing data -- excellent for Ads"))
                        return 0
        except (json.JSONDecodeError, TypeError):
            pass
    return 0


def analyze_ads_quality(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100

    score += _check_https(page, issues)
    load_speed_ms = page.elapsed_ms
    score += _check_load_speed(page, issues)
    score += _check_mobile_viewport(page, issues)
    content_penalty, word_count = _check_content_relevance(page, issues)
    score += content_penalty
    tracking_penalty, conversion_trackers = _check_conversion_tracking(page, issues)
    score += tracking_penalty
    cta_penalty, cta_count = _check_cta_and_forms(page, issues)
    score += cta_penalty
    score += _check_ad_schema(page, issues)

    metrics = {
        "https_compliant": page.scheme == "https",
        "load_speed_ms": load_speed_ms,
        "word_count": word_count,
        "cta_count": cta_count,
        "conversion_trackers": conversion_trackers,
    }

    return CategoryResult(name="ads_quality", score=max(0, min(100, score)), issues=issues, metrics=metrics)
