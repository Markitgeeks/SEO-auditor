"""SERP feature eligibility analysis."""

from __future__ import annotations

import json
import re

from app.models import CategoryResult, Issue
from app.fetcher import FetchResult

# Schema types mapped to SERP features
SCHEMA_SERP_MAP: dict[str, str] = {
    "Product": "Product Rich Snippet",
    "AggregateOffer": "Product Rich Snippet",
    "FAQPage": "FAQ Rich Result",
    "HowTo": "How-To Rich Result",
    "BreadcrumbList": "Breadcrumbs",
    "VideoObject": "Video Result",
    "LocalBusiness": "Local Pack / Knowledge Panel",
    "Restaurant": "Local Pack / Knowledge Panel",
    "Organization": "Knowledge Panel",
    "Person": "Knowledge Panel",
    "Article": "Article / Top Stories",
    "NewsArticle": "Top Stories",
    "BlogPosting": "Article Result",
    "Recipe": "Recipe Rich Result",
    "Event": "Event Rich Result",
    "Review": "Review Snippet",
    "AggregateRating": "Star Ratings",
    "SoftwareApplication": "Software Rich Result",
    "Course": "Course Rich Result",
    "JobPosting": "Job Listing",
}

MAX_FEATURES = 8  # normalizing denominator for scoring


def _extract_schema_types(soup) -> list[str]:
    """Extract all @type values from JSON-LD blocks."""
    types = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                # Handle @graph
                if "@graph" in item:
                    graph = item["@graph"]
                    if isinstance(graph, list):
                        for g in graph:
                            if isinstance(g, dict):
                                t = g.get("@type", "")
                                if isinstance(t, list):
                                    types.extend(t)
                                elif t:
                                    types.append(t)
                else:
                    t = item.get("@type", "")
                    if isinstance(t, list):
                        types.extend(t)
                    elif t:
                        types.append(t)
        except (json.JSONDecodeError, TypeError):
            pass
    return types


def _check_schema_features(soup, issues: list[Issue]) -> int:
    """Check which SERP features are eligible based on schema types."""
    types = _extract_schema_types(soup)
    features_found: set[str] = set()

    for schema_type in types:
        feature = SCHEMA_SERP_MAP.get(schema_type)
        if feature and feature not in features_found:
            features_found.add(feature)
            issues.append(Issue(severity="pass", message=f"Eligible: {feature} (via {schema_type} schema)"))

    if not types:
        issues.append(Issue(severity="warning", message="No schema markup found -- limits SERP feature eligibility"))

    return len(features_found)


def _check_sitelinks(soup, issues: list[Issue]) -> bool:
    """Check sitelinks eligibility: good navigation + internal links."""
    nav = soup.find("nav")
    nav_links = 0
    if nav:
        nav_links = len(nav.find_all("a", href=True))

    all_internal_links = len(soup.find_all("a", href=True))

    if nav and nav_links >= 4 and all_internal_links >= 10:
        issues.append(Issue(severity="pass", message=f"Sitelinks eligible: structured nav ({nav_links} links) + {all_internal_links} total links"))
        return True
    elif nav:
        issues.append(Issue(severity="info", message=f"Partial sitelinks eligibility: nav has {nav_links} links"))
        return False
    else:
        issues.append(Issue(severity="info", message="No <nav> element found -- sitelinks less likely"))
        return False


def _check_image_pack(soup, issues: list[Issue]) -> bool:
    """Check image pack eligibility: 3+ images with alt text."""
    images = soup.find_all("img")
    images_with_alt = [img for img in images if img.get("alt", "").strip()]

    if len(images_with_alt) >= 3:
        issues.append(Issue(severity="pass", message=f"Image pack eligible: {len(images_with_alt)} images with alt text"))
        return True
    elif images:
        issues.append(Issue(severity="info", message=f"Only {len(images_with_alt)}/{len(images)} images have alt text -- need 3+ for image pack"))
        return False
    return False


def _check_meta_robots(soup, issues: list[Issue]) -> int:
    """Check if meta robots blocks SERP features."""
    penalty = 0
    robots = soup.find("meta", attrs={"name": re.compile(r"robots", re.I)})
    if robots:
        content = robots.get("content", "").lower()
        if "noindex" in content:
            issues.append(Issue(severity="error", message="meta robots noindex -- page excluded from all SERP features"))
            penalty = -30
        if "nosnippet" in content:
            issues.append(Issue(severity="error", message="meta robots nosnippet -- rich snippets suppressed"))
            penalty = min(penalty, -20)
        if "max-snippet:0" in content.replace(" ", ""):
            issues.append(Issue(severity="warning", message="max-snippet:0 limits snippet display"))
            penalty = min(penalty, -10)
    return penalty


def _check_canonical(soup, page_url: str, issues: list[Issue]) -> int:
    """Check canonical tag consistency."""
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if canonical:
        href = canonical.get("href", "")
        if href and href.rstrip("/") != page_url.rstrip("/"):
            issues.append(Issue(severity="warning", message=f"Canonical URL differs from page URL -- SERP features may display for canonical instead"))
            return -5
        issues.append(Issue(severity="pass", message="Canonical URL matches page URL"))
    else:
        issues.append(Issue(severity="info", message="No canonical tag -- consider adding for SERP consistency"))
    return 0


def analyze_serp_features(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    soup = page.soup

    feature_count = _check_schema_features(soup, issues)

    if _check_sitelinks(soup, issues):
        feature_count += 1
    if _check_image_pack(soup, issues):
        feature_count += 1

    penalty = _check_meta_robots(soup, issues)
    penalty += _check_canonical(soup, page.url, issues)

    # Score: feature eligibility ratio + penalties
    raw_score = int((feature_count / MAX_FEATURES) * 100) + penalty
    score = max(0, min(100, raw_score))

    issues.insert(0, Issue(
        severity="info",
        message=f"Eligible for {feature_count} SERP feature(s) out of {MAX_FEATURES} checked"
    ))

    return CategoryResult(name="serp_features", score=score, issues=issues)
