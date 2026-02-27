"""ADA/WCAG accessibility analysis using the WAVE WebAIM API."""

from __future__ import annotations

import requests

from app.models import CategoryResult, Issue
from app.fetcher import FetchResult
from app.config import WAVE_API_KEY, WAVE_API_TIMEOUT


WAVE_API_URL = "https://wave.webaim.org/api/request"


def _call_wave_api(page_url: str) -> dict | None:
    """Call the WAVE API and return parsed JSON, or None on failure."""
    try:
        resp = requests.get(
            WAVE_API_URL,
            params={
                "key": WAVE_API_KEY,
                "url": page_url,
                "format": "json",
                "reporttype": "2",
            },
            timeout=WAVE_API_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("status", {}).get("success", False):
            return None
        return data
    except (requests.RequestException, ValueError):
        return None


def _analyze_category(cat_key: str, cat_data: dict, issues: list[Issue]) -> int:
    """Analyze a single WAVE category and return penalty points."""
    count = cat_data.get("count", 0)
    items = cat_data.get("items", {})

    if cat_key == "error":
        if count == 0:
            issues.append(Issue(severity="pass", message="No accessibility errors detected"))
            return 0
        penalty = min(count * 3, 40)
        issues.append(Issue(severity="error", message=f"{count} accessibility error(s) found"))
        for item_id, item_data in list(items.items())[:8]:
            item_count = item_data.get("count", 1)
            desc = item_data.get("description", item_id)
            issues.append(Issue(
                severity="error",
                message=f"{desc} ({item_count} instance(s))"
            ))
        return -penalty

    elif cat_key == "contrast":
        if count == 0:
            issues.append(Issue(severity="pass", message="No contrast issues detected"))
            return 0
        penalty = min(count * 2, 20)
        issues.append(Issue(severity="warning", message=f"{count} contrast issue(s) found"))
        for item_id, item_data in list(items.items())[:5]:
            item_count = item_data.get("count", 1)
            desc = item_data.get("description", item_id)
            issues.append(Issue(
                severity="warning",
                message=f"{desc} ({item_count} instance(s))"
            ))
        return -penalty

    elif cat_key == "alert":
        if count == 0:
            issues.append(Issue(severity="pass", message="No accessibility alerts"))
            return 0
        penalty = min(count, 15)
        issues.append(Issue(severity="warning", message=f"{count} accessibility alert(s)"))
        for item_id, item_data in list(items.items())[:5]:
            item_count = item_data.get("count", 1)
            desc = item_data.get("description", item_id)
            issues.append(Issue(
                severity="info",
                message=f"{desc} ({item_count} instance(s))"
            ))
        return -penalty

    elif cat_key == "feature":
        if count > 0:
            issues.append(Issue(severity="pass", message=f"{count} accessibility feature(s) detected (alt text, labels, etc.)"))
        return 0

    elif cat_key == "structure":
        if count > 0:
            issues.append(Issue(severity="pass", message=f"{count} structural element(s) found (headings, nav, landmarks)"))
        return 0

    elif cat_key == "aria":
        if count > 0:
            issues.append(Issue(severity="pass", message=f"{count} ARIA attribute(s) in use"))
        return 0

    return 0


def analyze_accessibility(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100

    data = _call_wave_api(page.url)

    if data is None:
        issues.append(Issue(severity="warning", message="Could not reach WAVE API -- accessibility analysis unavailable"))
        return CategoryResult(name="accessibility", score=50, issues=issues)

    # Statistics
    stats = data.get("statistics", {})
    page_title = stats.get("pagetitle", "")
    credits = stats.get("creditsremaining", "?")
    issues.append(Issue(severity="info", message=f"WAVE analysis complete (credits remaining: {credits})"))

    # Process each WAVE category
    categories = data.get("categories", {})
    for cat_key in ["error", "contrast", "alert", "feature", "structure", "aria"]:
        cat_data = categories.get(cat_key, {})
        penalty = _analyze_category(cat_key, cat_data, issues)
        score += penalty

    return CategoryResult(name="accessibility", score=max(0, min(100, score)), issues=issues)
