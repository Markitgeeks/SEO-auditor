"""Sitemap-to-Spreadsheet Export: discovers sitemaps, parses URLs, fetches metadata."""

import asyncio
import gzip
import io
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse, urljoin

import certifi
import requests
from bs4 import BeautifulSoup

from app.config import USER_AGENT
from app.services.job_manager import get_job, update_job, JobStatus
from app.exporters.spreadsheet import generate_sitemap_xlsx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15
HEAD_TIMEOUT = 10
BATCH_SIZE = 20
MAX_WORKERS = 5
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]


class SitemapExportConfig:
    def __init__(self, max_urls=5000, batch_delay_ms=200, max_concurrent=5,
                 include_word_count=True, include_og_tags=True,
                 respect_robots=True, retry_count=3):
        self.max_urls = max_urls
        self.batch_delay_ms = batch_delay_ms
        self.max_concurrent = max_concurrent
        self.include_word_count = include_word_count
        self.include_og_tags = include_og_tags
        self.respect_robots = respect_robots
        self.retry_count = retry_count


def _headers():
    return {"User-Agent": USER_AGENT}


def _normalize_url(url: str) -> str:
    """Normalize URL for deduplication: lowercase host, strip fragment, trailing slash."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{host}{path}"


def _fetch_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[requests.Response]:
    try:
        resp = requests.get(url, headers=_headers(), timeout=timeout,
                            allow_redirects=True, verify=certifi.where())
        return resp
    except requests.RequestException:
        return None


def discover_sitemaps(domain: str) -> list[str]:
    """Discover sitemap URLs from robots.txt and common paths."""
    base = f"https://{domain}" if not domain.startswith("http") else domain
    parsed = urlparse(base)
    base = f"{parsed.scheme}://{parsed.netloc}"

    sitemap_urls = set()

    # 1. Check robots.txt
    robots_resp = _fetch_url(f"{base}/robots.txt", timeout=10)
    if robots_resp and robots_resp.status_code == 200:
        for line in robots_resp.text.splitlines():
            line = line.strip()
            if line.lower().startswith("sitemap:"):
                url = line.split(":", 1)[1].strip()
                if url:
                    sitemap_urls.add(url)

    # 2. Try common sitemap paths
    common_paths = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml", "/wp-sitemap.xml"]
    for path in common_paths:
        url = f"{base}{path}"
        if url not in sitemap_urls:
            resp = _fetch_url(url, timeout=10)
            if resp and resp.status_code == 200 and "xml" in resp.headers.get("content-type", "").lower():
                sitemap_urls.add(url)
                break  # found one, don't try more

    return list(sitemap_urls)


def parse_sitemap_recursive(url: str, seen_urls: set, max_depth: int = 3, depth: int = 0) -> list[dict]:
    """Parse a sitemap (or sitemap index) recursively. Returns list of URL entries."""
    if depth > max_depth:
        return []

    resp = _fetch_url(url, timeout=15)
    if not resp or resp.status_code != 200:
        return []

    content = resp.content
    # Handle gzip
    if url.endswith(".gz") or resp.headers.get("Content-Encoding") == "gzip":
        try:
            content = gzip.decompress(content)
        except Exception:
            pass

    try:
        soup = BeautifulSoup(content, "lxml-xml")
    except Exception:
        try:
            soup = BeautifulSoup(content, "html.parser")
        except Exception:
            return []

    entries = []

    # Check if sitemap index
    sub_sitemaps = soup.find_all("sitemap")
    if sub_sitemaps:
        for sm in sub_sitemaps:
            loc = sm.find("loc")
            if loc:
                child_url = loc.get_text(strip=True)
                entries.extend(parse_sitemap_recursive(child_url, seen_urls, max_depth, depth + 1))
        return entries

    # Regular urlset
    url_entries = soup.find_all("url")
    for entry in url_entries:
        loc = entry.find("loc")
        if not loc:
            continue
        raw_url = loc.get_text(strip=True)
        normalized = _normalize_url(raw_url)
        if normalized in seen_urls:
            continue
        seen_urls.add(normalized)

        lastmod_tag = entry.find("lastmod")
        changefreq_tag = entry.find("changefreq")
        priority_tag = entry.find("priority")

        entries.append({
            "url": raw_url,
            "lastmod": lastmod_tag.get_text(strip=True) if lastmod_tag else "",
            "changefreq": changefreq_tag.get_text(strip=True) if changefreq_tag else "",
            "priority": priority_tag.get_text(strip=True) if priority_tag else "",
        })

    return entries


def parse_robots_txt(domain: str) -> list[dict]:
    """Parse robots.txt and return disallow rules for * and SEOAuditor."""
    base = f"https://{domain}" if not domain.startswith("http") else domain
    parsed = urlparse(base)
    base = f"{parsed.scheme}://{parsed.netloc}"

    resp = _fetch_url(f"{base}/robots.txt", timeout=10)
    if not resp or resp.status_code != 200:
        return []

    rules = []
    current_agents = []
    for line in resp.text.splitlines():
        line = line.strip()
        if line.lower().startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip().lower()
            current_agents = [agent]
        elif line.lower().startswith("disallow:"):
            path = line.split(":", 1)[1].strip()
            if path and any(a in ("*", "seoauditor") for a in current_agents):
                rules.append({"path": path})
    return rules


def _is_disallowed(url: str, rules: list[dict]) -> bool:
    parsed = urlparse(url)
    path = parsed.path
    for rule in rules:
        rule_path = rule["path"]
        if rule_path.endswith("*"):
            if path.startswith(rule_path[:-1]):
                return True
        elif path.startswith(rule_path):
            return True
    return False


def _fetch_metadata(entry: dict, robots_rules: list[dict], config: SitemapExportConfig) -> dict:
    """Fetch and extract metadata for a single URL."""
    url = entry["url"]
    result = {
        "url": url,
        "lastmod": entry.get("lastmod", ""),
        "changefreq": entry.get("changefreq", ""),
        "priority": entry.get("priority", ""),
        "robots_txt_status": "Disallowed" if _is_disallowed(url, robots_rules) else "Allowed",
    }

    # HEAD request first
    try:
        head_resp = requests.head(url, headers=_headers(), timeout=HEAD_TIMEOUT,
                                  allow_redirects=True, verify=certifi.where())
        result["status_code"] = head_resp.status_code
        result["content_type"] = head_resp.headers.get("content-type", "")
    except requests.RequestException as e:
        result["status_code"] = 0
        result["content_type"] = ""
        result["extraction_method"] = "failed"
        result["error"] = str(e)[:200]
        return result

    # Only fetch full HTML for 200 text/html pages
    if result["status_code"] == 200 and "text/html" in result.get("content_type", ""):
        for attempt in range(config.retry_count):
            try:
                resp = requests.get(url, headers=_headers(), timeout=DEFAULT_TIMEOUT,
                                    allow_redirects=True, verify=certifi.where())
                soup = BeautifulSoup(resp.content, "lxml")

                # Title
                title_tag = soup.find("title")
                title = title_tag.get_text(strip=True) if title_tag else ""
                result["title"] = title[:500]
                result["title_length"] = len(title)

                # Meta description
                desc_tag = soup.find("meta", attrs={"name": "description"})
                desc = desc_tag.get("content", "") if desc_tag else ""
                result["meta_description"] = desc[:500]
                result["description_length"] = len(desc)

                # H1
                h1_tag = soup.find("h1")
                result["h1"] = h1_tag.get_text(strip=True)[:300] if h1_tag else ""

                # Canonical
                canon_tag = soup.find("link", attrs={"rel": "canonical"})
                canonical = canon_tag.get("href", "") if canon_tag else ""
                result["canonical"] = canonical
                if not canonical:
                    result["canonical_match"] = "missing"
                elif _normalize_url(canonical) == _normalize_url(url):
                    result["canonical_match"] = "match"
                else:
                    result["canonical_match"] = "mismatch"

                # Robots meta
                robots_meta = soup.find("meta", attrs={"name": "robots"})
                robots_content = robots_meta.get("content", "") if robots_meta else ""
                result["robots_meta"] = robots_content

                # Indexability
                noindex = "noindex" in robots_content.lower()
                disallowed = result["robots_txt_status"] == "Disallowed"
                result["is_indexable"] = "No" if (noindex or disallowed) else "Yes"

                # Word count
                if config.include_word_count:
                    text = soup.get_text(separator=" ", strip=True)
                    result["word_count"] = len(text.split())

                # OG tags
                if config.include_og_tags:
                    og_title = soup.find("meta", attrs={"property": "og:title"})
                    og_desc = soup.find("meta", attrs={"property": "og:description"})
                    result["og_title"] = og_title.get("content", "")[:500] if og_title else ""
                    result["og_description"] = og_desc.get("content", "")[:500] if og_desc else ""

                result["extraction_method"] = "html_parse"

                # Notes
                notes = []
                if not title:
                    notes.append("Missing title")
                if not desc:
                    notes.append("Missing description")
                if not h1_tag:
                    notes.append("Missing H1")
                if not canonical:
                    notes.append("Missing canonical")
                result["notes"] = ", ".join(notes)

                break  # success
            except requests.exceptions.HTTPError as e:
                if e.response and e.response.status_code in (429, 500, 502, 503, 504):
                    if attempt < config.retry_count - 1:
                        time.sleep(RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)])
                        continue
                result["extraction_method"] = "failed"
                result["error"] = str(e)[:200]
                break
            except Exception as e:
                result["extraction_method"] = "failed"
                result["error"] = str(e)[:200]
                break
    else:
        result["extraction_method"] = "failed" if result["status_code"] != 200 else "non_html"
        notes = []
        if result["status_code"] >= 300 and result["status_code"] < 400:
            notes.append("Redirect")
        elif result["status_code"] >= 400:
            notes.append(f"HTTP {result['status_code']}")
        result["notes"] = ", ".join(notes)
        result["is_indexable"] = "No" if result["status_code"] != 200 else "Unknown"

    return result


def compute_summary(results: list[dict]) -> dict:
    total = len(results)
    fetched_ok = sum(1 for r in results if r.get("extraction_method") != "failed")
    failed = total - fetched_ok
    status_200 = sum(1 for r in results if r.get("status_code") == 200)
    status_301 = sum(1 for r in results if r.get("status_code") in (301, 302))
    status_404 = sum(1 for r in results if r.get("status_code") == 404)
    status_5xx = sum(1 for r in results if isinstance(r.get("status_code"), int) and 500 <= r["status_code"] < 600)
    missing_title = sum(1 for r in results if not r.get("title"))
    missing_desc = sum(1 for r in results if not r.get("meta_description"))
    missing_h1 = sum(1 for r in results if not r.get("h1"))
    missing_canon = sum(1 for r in results if r.get("canonical_match") == "missing")
    non_indexable = sum(1 for r in results if r.get("is_indexable") == "No")
    word_counts = [r["word_count"] for r in results if r.get("word_count")]
    avg_wc = int(sum(word_counts) / len(word_counts)) if word_counts else 0

    return {
        "total_urls": total,
        "fetched_ok": fetched_ok,
        "failed": failed,
        "status_200": status_200,
        "status_301": status_301,
        "status_404": status_404,
        "status_5xx": status_5xx,
        "missing_title": missing_title,
        "missing_description": missing_desc,
        "missing_h1": missing_h1,
        "missing_canonical": missing_canon,
        "non_indexable": non_indexable,
        "avg_word_count": avg_wc,
    }


async def run_sitemap_export(job_id: str, domain: str, config: SitemapExportConfig):
    """Main sitemap export pipeline. Runs as an asyncio task."""
    try:
        update_job(job_id, status=JobStatus.RUNNING, progress_message="Discovering sitemaps...")

        # Step 1: Discover
        sitemap_urls = await asyncio.get_event_loop().run_in_executor(
            None, discover_sitemaps, domain
        )
        if not sitemap_urls:
            update_job(job_id, status=JobStatus.FAILED,
                       error_message="No sitemaps found. Tried robots.txt and common sitemap paths.")
            return

        # Step 2: Parse all sitemaps
        update_job(job_id, progress_message=f"Parsing {len(sitemap_urls)} sitemap(s)...")
        all_entries = []
        seen_urls = set()

        def _parse_all():
            for sm_url in sitemap_urls:
                entries = parse_sitemap_recursive(sm_url, seen_urls, max_depth=3)
                all_entries.extend(entries)
                if len(all_entries) >= config.max_urls:
                    return all_entries[:config.max_urls]
            return all_entries

        all_entries = await asyncio.get_event_loop().run_in_executor(None, _parse_all)

        if not all_entries:
            update_job(job_id, status=JobStatus.FAILED,
                       error_message="Sitemaps found but contained no URL entries.")
            return

        update_job(job_id, total_items=len(all_entries),
                   progress_message=f"Found {len(all_entries)} URLs. Fetching metadata...")

        # Step 3: Robots.txt rules
        robots_rules = await asyncio.get_event_loop().run_in_executor(
            None, parse_robots_txt, domain
        )

        # Step 4: Fetch metadata in batches
        results = []
        errors = []
        batch_size = BATCH_SIZE
        loop = asyncio.get_event_loop()

        for i in range(0, len(all_entries), batch_size):
            batch = all_entries[i:i + batch_size]

            def _fetch_batch(batch=batch):
                batch_results = []
                with ThreadPoolExecutor(max_workers=config.max_concurrent) as executor:
                    futures = {
                        executor.submit(_fetch_metadata, entry, robots_rules, config): entry
                        for entry in batch
                    }
                    for future in as_completed(futures):
                        try:
                            batch_results.append(future.result())
                        except Exception as e:
                            entry = futures[future]
                            batch_results.append({
                                "url": entry["url"],
                                "extraction_method": "failed",
                                "error": str(e)[:200],
                            })
                return batch_results

            batch_results = await loop.run_in_executor(None, _fetch_batch)
            results.extend(batch_results)

            # Track errors
            for r in batch_results:
                if r.get("error"):
                    errors.append({"url": r["url"], "error": r["error"]})

            completed = len(results)
            failed = sum(1 for r in results if r.get("extraction_method") == "failed")
            update_job(
                job_id,
                completed_items=completed,
                failed_items=failed,
                progress=completed / len(all_entries),
                progress_message=f"Fetched {completed}/{len(all_entries)} URLs",
                errors=errors[-50:],  # keep last 50
            )

            await asyncio.sleep(config.batch_delay_ms / 1000)

        # Step 5: Generate XLSX
        update_job(job_id, progress_message="Generating spreadsheet...")
        summary = compute_summary(results)

        xlsx_path = await loop.run_in_executor(
            None, generate_sitemap_xlsx, results, domain, summary
        )

        update_job(
            job_id,
            status=JobStatus.COMPLETED,
            result_path=xlsx_path,
            result_data=summary,
            progress=1.0,
            progress_message="Export complete",
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        logger.exception("Sitemap export failed for job %s", job_id)
        update_job(job_id, status=JobStatus.FAILED, error_message=str(e)[:500])
