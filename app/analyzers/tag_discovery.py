"""Deep tag/pixel scanner: multi-page scanning with cross-page analysis."""

import asyncio
import logging
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse, urljoin

import certifi
import requests
from bs4 import BeautifulSoup

from app.config import USER_AGENT
from app.services.job_manager import get_job, update_job, JobStatus
from app.exporters.spreadsheet import generate_tags_xlsx
from app.analyzers.tag_signatures import TAG_SIGNATURES, TagSignature

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15

PAGE_TYPES = [
    {"type": "homepage", "url": "/"},
    {"type": "collection", "url": "/collections", "fallback": "/collections/all"},
    {"type": "product", "url": None, "discover": True},
    {"type": "cart", "url": "/cart"},
    {"type": "blog", "url": "/blogs", "fallback": "/blogs/news"},
    {"type": "page", "url": "/pages/about", "fallback": "/pages/contact"},
]


class TagScanConfig:
    def __init__(self, page_types=None, redact_mode=False, max_pages=6):
        self.page_types = page_types or ["homepage", "product", "collection", "cart"]
        self.redact_mode = redact_mode
        self.max_pages = max_pages


def _headers():
    return {"User-Agent": USER_AGENT}


def _fetch_html(url: str) -> Optional[tuple[str, BeautifulSoup]]:
    try:
        resp = requests.get(url, headers=_headers(), timeout=DEFAULT_TIMEOUT,
                            allow_redirects=True, verify=certifi.where())
        if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
            soup = BeautifulSoup(resp.content, "lxml")
            return resp.text, soup
    except requests.RequestException:
        pass
    return None


def _discover_product_url(base_url: str, soup: BeautifulSoup) -> Optional[str]:
    """Find first product URL from homepage links."""
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/products/" in href and "/products/?" not in href:
            if href.startswith("/"):
                return urljoin(base_url, href)
            elif href.startswith("http"):
                return href
    return None


def _resolve_page_urls(domain: str, requested_types: list[str]) -> list[dict]:
    """Resolve actual URLs for requested page types."""
    base = f"https://{domain}" if not domain.startswith("http") else domain
    parsed = urlparse(base)
    base = f"{parsed.scheme}://{parsed.netloc}"

    # Fetch homepage first (needed for product discovery)
    homepage_result = _fetch_html(base + "/")
    homepage_soup = homepage_result[1] if homepage_result else None

    pages = []
    for pt in PAGE_TYPES:
        if pt["type"] not in requested_types:
            continue

        if pt.get("discover") and pt["type"] == "product":
            # Discover product URL from homepage
            if homepage_soup:
                product_url = _discover_product_url(base, homepage_soup)
                if product_url:
                    pages.append({"type": "product", "url": product_url})
                    continue
            pages.append({"type": "product", "url": None, "status": "skipped",
                          "error": "No product URL found"})
            continue

        url = base + pt["url"] if pt.get("url") else None
        if url:
            result = _fetch_html(url)
            if result:
                pages.append({"type": pt["type"], "url": url})
                continue
            # Try fallback
            fallback = pt.get("fallback")
            if fallback:
                url = base + fallback
                result = _fetch_html(url)
                if result:
                    pages.append({"type": pt["type"], "url": url})
                    continue
        pages.append({"type": pt["type"], "url": url, "status": "skipped",
                      "error": "Page not accessible"})

    return pages


def _scan_page(url: str) -> Optional[dict]:
    """Scan a single page for tags. Returns raw detection data."""
    result = _fetch_html(url)
    if not result:
        return None

    html_text, soup = result

    # Collect script info
    head = soup.find("head")
    body = soup.find("body")

    script_data = []
    for script in soup.find_all("script"):
        src = script.get("src", "")
        is_async = script.has_attr("async")
        is_defer = script.has_attr("defer")
        inline_text = script.get_text() if not src else ""
        location = "head" if (head and script in head.descendants) else "body"

        script_data.append({
            "src": src,
            "inline": inline_text[:2000],
            "async": is_async,
            "defer": is_defer,
            "location": location,
        })

    # Concatenated inline JS
    all_inline = " ".join(s["inline"] for s in script_data if s["inline"])
    all_srcs = [s["src"] for s in script_data if s["src"]]

    # Noscript content
    noscript_content = " ".join(ns.get_text() for ns in soup.find_all("noscript"))

    # Detect tags
    detections = []
    for sig in TAG_SIGNATURES:
        matched = False
        match_src = ""
        match_method = ""
        match_location = ""
        match_snippet = ""
        is_async_defer = "N/A"

        # Check URL patterns
        for src in all_srcs:
            for pattern in sig.url_patterns:
                if pattern in src:
                    matched = True
                    match_src = src
                    match_method = "direct_script"
                    # Find the script element for location info
                    for sd in script_data:
                        if sd["src"] == src:
                            match_location = sd["location"]
                            if sd["async"]:
                                is_async_defer = "async"
                            elif sd["defer"]:
                                is_async_defer = "defer"
                            else:
                                is_async_defer = "blocking"
                            break
                    break
            if matched:
                break

        # Check inline patterns
        if not matched:
            for pattern in sig.inline_patterns:
                if pattern in all_inline:
                    matched = True
                    match_method = "inline"
                    match_location = "inline"
                    is_async_defer = "N/A"
                    # Extract snippet around the match
                    idx = all_inline.find(pattern)
                    start = max(0, idx - 50)
                    match_snippet = all_inline[start:idx + 200]
                    break

        # Check noscript patterns
        if not matched:
            for pattern in sig.noscript_patterns:
                if pattern in noscript_content:
                    matched = True
                    match_method = "noscript_fallback"
                    match_location = "noscript"
                    is_async_defer = "N/A"
                    break

        if matched:
            # Extract ID(s)
            search_text = match_src + " " + all_inline + " " + noscript_content
            ids = sig.id_pattern.findall(search_text)
            tag_id = ids[0] if ids else ""

            detections.append({
                "vendor": sig.vendor,
                "vendor_short": sig.vendor_short,
                "category": sig.category,
                "tag_id": tag_id,
                "load_method": match_method,
                "dom_location": match_location,
                "script_url": match_src,
                "code_snippet": match_snippet[:500],
                "async_defer": is_async_defer,
                "impact": sig.load_impact,
                "is_essential": sig.is_essential,
            })

    return {"url": url, "detections": detections}


def _merge_results(page_scans: list[dict]) -> list[dict]:
    """Merge tag detections across pages into unified tag list."""
    # Key: (vendor_short, tag_id)
    tag_map = defaultdict(lambda: {
        "pages": [],
        "data": None,
        "same_page_count": defaultdict(int),
    })

    for scan in page_scans:
        url = scan["url"]
        page_type = scan.get("page_type", "unknown")
        seen_on_page = set()

        for det in scan["detections"]:
            key = (det["vendor_short"], det["tag_id"])
            if key not in seen_on_page:
                tag_map[key]["pages"].append(page_type)
                seen_on_page.add(key)
            else:
                tag_map[key]["same_page_count"][page_type] += 1

            if tag_map[key]["data"] is None:
                tag_map[key]["data"] = det

    merged = []
    for (vendor_short, tag_id), info in tag_map.items():
        det = info["data"]
        pages = info["pages"]
        same_page_dupes = info["same_page_count"]

        is_duplicate = "No"
        if same_page_dupes:
            pages_with_dupes = [f"{p} ({c + 1}x)" for p, c in same_page_dupes.items()]
            is_duplicate = f"Yes - same page ({', '.join(pages_with_dupes)})"

        impact_detail = ""
        if det["async_defer"] == "blocking":
            impact_detail = "Render-blocking script in <head>"
        elif det["impact"] == "high":
            impact_detail = "High resource usage"

        merged.append({
            "vendor": det["vendor"],
            "vendor_short": det["vendor_short"],
            "category": det["category"],
            "tag_id": tag_id,
            "pages_found_on": ", ".join(pages),
            "page_count": len(pages),
            "load_method": det["load_method"],
            "dom_location": det["dom_location"],
            "script_url": det["script_url"],
            "code_snippet": det["code_snippet"],
            "async_defer": det["async_defer"],
            "is_duplicate": is_duplicate,
            "impact": det["impact"],
            "impact_detail": impact_detail,
            "notes": "",
        })

    return merged


def _generate_recommendations(merged_tags: list[dict], page_coverage: list[dict]) -> list[dict]:
    """Generate actionable recommendations from scan results."""
    recs = []
    vendors_found = {t["vendor_short"] for t in merged_tags}
    total_pages = sum(1 for p in page_coverage if p.get("status") == "scanned")

    # Missing essentials
    if "GTM" not in vendors_found:
        recs.append({
            "priority": "High",
            "category": "Missing",
            "recommendation": "No Google Tag Manager detected. GTM enables centralized tag management and reduces developer dependency for marketing tags.",
            "affected_tags": "GTM",
            "expected_impact": "Simplified tag management, faster tag deployment",
        })

    if "GA4" not in vendors_found and "UA" not in vendors_found:
        recs.append({
            "priority": "Critical",
            "category": "Missing",
            "recommendation": "No Google Analytics detected. Install GA4 to track site traffic, user behavior, and conversion data.",
            "affected_tags": "GA4",
            "expected_impact": "Enable traffic and conversion tracking",
        })

    # Duplicate detection
    for tag in merged_tags:
        if tag["is_duplicate"] != "No":
            recs.append({
                "priority": "High",
                "category": "Duplication",
                "recommendation": f"{tag['vendor']} ({tag['tag_id']}) is loaded multiple times on the same page. This causes duplicate data and inflated metrics.",
                "affected_tags": f"{tag['vendor_short']} - {tag['tag_id']}",
                "expected_impact": "Fix data accuracy, reduce page load",
            })

    # Render-blocking scripts
    blocking = [t for t in merged_tags if t["async_defer"] == "blocking"]
    if blocking:
        vendors = ", ".join(f"{t['vendor_short']}" for t in blocking)
        recs.append({
            "priority": "High",
            "category": "Performance",
            "recommendation": f"Render-blocking scripts detected: {vendors}. Add async or defer attributes to prevent blocking page render.",
            "affected_tags": vendors,
            "expected_impact": "Reduce page load time by 100-500ms",
        })

    # Consolidation into GTM
    if "GTM" in vendors_found:
        direct_tags = [t for t in merged_tags
                       if t["load_method"] == "direct_script"
                       and t["vendor_short"] != "GTM"]
        if direct_tags:
            vendors = ", ".join(f"{t['vendor_short']}" for t in direct_tags[:5])
            recs.append({
                "priority": "Medium",
                "category": "Consolidation",
                "recommendation": f"Tags loaded directly instead of through GTM: {vendors}. Migrate these into GTM for centralized management.",
                "affected_tags": vendors,
                "expected_impact": "Easier tag management, single point of control",
            })

    # Inconsistent coverage: tag on homepage but missing elsewhere
    for tag in merged_tags:
        if tag["page_count"] < total_pages and total_pages > 1:
            pages_on = tag["pages_found_on"]
            if "homepage" in pages_on and tag["category"] == "advertising":
                recs.append({
                    "priority": "Critical",
                    "category": "Missing",
                    "recommendation": f"{tag['vendor']} ({tag['tag_id']}) found on {pages_on} but missing on other pages. This breaks conversion tracking for pages without the tag.",
                    "affected_tags": f"{tag['vendor_short']} - {tag['tag_id']}",
                    "expected_impact": "Fix conversion attribution",
                })

    # Legacy UA
    if "UA" in vendors_found:
        recs.append({
            "priority": "Medium",
            "category": "Consolidation",
            "recommendation": "Legacy Universal Analytics (UA) detected. UA was sunset in July 2023. Migrate to GA4.",
            "affected_tags": "UA",
            "expected_impact": "Ensure continued analytics data collection",
        })

    return recs


def _build_page_coverage(pages: list[dict], page_scans: list[dict]) -> list[dict]:
    """Build page coverage report."""
    scan_map = {s["url"]: s for s in page_scans}
    coverage = []

    for page in pages:
        url = page.get("url", "")
        scan = scan_map.get(url)
        status = page.get("status", "scanned" if scan else "skipped")

        entry = {
            "page_type": page["type"],
            "url": url or "N/A",
            "status": status,
            "tags_found": len(scan["detections"]) if scan else 0,
            "gtm": "No",
            "ga4": "No",
            "meta_pixel": "No",
            "other_tags": "",
        }

        if scan:
            vendor_shorts = {d["vendor_short"] for d in scan["detections"]}
            entry["gtm"] = "Yes" if "GTM" in vendor_shorts else "No"
            entry["ga4"] = "Yes" if "GA4" in vendor_shorts else "No"
            entry["meta_pixel"] = "Yes" if "FBP" in vendor_shorts else "No"
            others = vendor_shorts - {"GTM", "GA4", "FBP"}
            entry["other_tags"] = ", ".join(sorted(others))

        coverage.append(entry)

    return coverage


def _redact_id(tag_id: str) -> str:
    """Redact tag ID: show first 30%, mask rest with *."""
    if not tag_id:
        return tag_id
    show = max(1, int(len(tag_id) * 0.3))
    return tag_id[:show] + "*" * (len(tag_id) - show)


async def run_tag_scan(job_id: str, domain: str, config: TagScanConfig):
    """Main tag discovery pipeline. Runs as an asyncio task."""
    try:
        update_job(job_id, status=JobStatus.RUNNING,
                   progress_message="Resolving page URLs...")

        loop = asyncio.get_event_loop()

        # Step 1: Resolve page URLs
        pages = await loop.run_in_executor(
            None, _resolve_page_urls, domain, config.page_types
        )

        scannable = [p for p in pages if p.get("status") != "skipped" and p.get("url")]
        update_job(job_id, total_items=len(scannable),
                   progress_message=f"Scanning {len(scannable)} pages...")

        # Step 2: Scan each page
        page_scans = []
        for i, page in enumerate(scannable):
            update_job(job_id,
                       completed_items=i,
                       progress=(i / len(scannable)) if scannable else 0,
                       progress_message=f"Scanning {page['type']}: {page['url']}")

            scan_result = await loop.run_in_executor(None, _scan_page, page["url"])
            if scan_result:
                scan_result["page_type"] = page["type"]
                page_scans.append(scan_result)

        # Step 3: Cross-page analysis
        update_job(job_id, progress_message="Analyzing results...")
        merged_tags = _merge_results(page_scans)

        # Step 4: Page coverage
        page_coverage = _build_page_coverage(pages, page_scans)

        # Step 5: Recommendations
        recommendations = _generate_recommendations(merged_tags, page_coverage)

        # Apply redaction if requested
        if config.redact_mode:
            for tag in merged_tags:
                tag["tag_id"] = _redact_id(tag["tag_id"])
                if tag.get("code_snippet") and tag.get("tag_id"):
                    tag["code_snippet"] = "[REDACTED]"

        # Step 6: Generate XLSX
        update_job(job_id, progress_message="Generating spreadsheet...")
        xlsx_path = await loop.run_in_executor(
            None, generate_tags_xlsx, merged_tags, recommendations, page_coverage, domain
        )

        result_data = {
            "domain": domain,
            "pages_scanned": len(page_scans),
            "tags_found": len(merged_tags),
            "tags": merged_tags,
            "recommendations": recommendations,
            "page_coverage": page_coverage,
        }

        update_job(
            job_id,
            status=JobStatus.COMPLETED,
            result_path=xlsx_path,
            result_data=result_data,
            progress=1.0,
            progress_message="Scan complete",
            completed_items=len(scannable),
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        logger.exception("Tag scan failed for job %s", job_id)
        update_job(job_id, status=JobStatus.FAILED, error_message=str(e)[:500])
