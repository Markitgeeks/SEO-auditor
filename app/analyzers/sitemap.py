from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

from app.models import CategoryResult, Issue
from app.config import SECONDARY_TIMEOUT, USER_AGENT
from app.fetcher import FetchResult

MAX_URLS_TO_PARSE = 500


def _fetch_xml(url: str) -> requests.Response | None:
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=SECONDARY_TIMEOUT,
            allow_redirects=True,
        )
        if resp.status_code == 200 and "xml" in resp.headers.get("content-type", "").lower():
            return resp
    except requests.RequestException:
        pass
    return None


def analyze_sitemap(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    base = page.base_url
    sitemap_url = f"{base}/sitemap.xml"

    try:
        resp = requests.get(
            sitemap_url,
            headers={"User-Agent": USER_AGENT},
            timeout=SECONDARY_TIMEOUT,
            allow_redirects=True,
        )
    except requests.RequestException as e:
        issues.append(Issue(severity="error", message=f"Could not fetch sitemap.xml: {str(e)[:100]}"))
        return CategoryResult(name="sitemap", score=max(0, score - 40), issues=issues)

    if resp.status_code != 200:
        issues.append(Issue(severity="error", message=f"sitemap.xml not found (HTTP {resp.status_code})"))
        return CategoryResult(name="sitemap", score=max(0, score - 40), issues=issues)

    if "xml" not in resp.headers.get("content-type", "").lower():
        issues.append(Issue(severity="warning", message="sitemap.xml exists but content-type is not XML"))
        return CategoryResult(name="sitemap", score=max(0, score - 20), issues=issues)

    issues.append(Issue(severity="pass", message=f"sitemap.xml found at {sitemap_url}"))
    sitemap_soup = BeautifulSoup(resp.content, "lxml-xml")

    # Detect sitemap index vs regular sitemap
    sub_sitemaps = sitemap_soup.find_all("sitemap")
    url_entries = sitemap_soup.find_all("url")

    if sub_sitemaps:
        # --- Sitemap Index ---
        sub_locs = [s.find("loc") for s in sub_sitemaps]
        sub_urls = [loc.get_text(strip=True) for loc in sub_locs if loc]
        issues.append(Issue(severity="info", message=f"Sitemap index with {len(sub_urls)} sub-sitemap(s)"))

        # Parse up to a few sub-sitemaps to count total URLs
        total_urls = 0
        for sub_url in sub_urls[:5]:
            sub_resp = _fetch_xml(sub_url)
            if sub_resp:
                sub_soup = BeautifulSoup(sub_resp.content, "lxml-xml")
                count = len(sub_soup.find_all("url"))
                total_urls += count
                if total_urls >= MAX_URLS_TO_PARSE:
                    break
        if total_urls:
            issues.append(Issue(severity="info", message=f"~{total_urls}+ URLs across parsed sub-sitemaps"))

        # Use sub-sitemap locs for URL-in-sitemap check
        all_locs = sub_urls
    elif url_entries:
        # --- Regular sitemap ---
        issues.append(Issue(severity="info", message=f"Sitemap contains {len(url_entries)} URL entries"))
        all_locs = [loc.get_text(strip=True) for u in url_entries for loc in (u.find("loc"),) if loc]

        # --- Check <lastmod> freshness ---
        lastmods = [u.find("lastmod") for u in url_entries]
        lastmod_texts = [lm.get_text(strip=True) for lm in lastmods if lm]
        if lastmod_texts:
            issues.append(Issue(severity="pass", message=f"{len(lastmod_texts)}/{len(url_entries)} URLs have <lastmod>"))
            stale_count = 0
            now = datetime.now(timezone.utc)
            for dt_str in lastmod_texts:
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    if (now - dt).days > 365:
                        stale_count += 1
                except (ValueError, TypeError):
                    pass
            if stale_count:
                issues.append(Issue(severity="warning", message=f"{stale_count} URL(s) have <lastmod> older than 1 year"))
                score -= 10
        else:
            issues.append(Issue(severity="info", message="No <lastmod> dates in sitemap"))

        # --- Check <changefreq> and <priority> ---
        changefreqs = [u.find("changefreq") for u in url_entries if u.find("changefreq")]
        priorities = [u.find("priority") for u in url_entries if u.find("priority")]
        if changefreqs:
            issues.append(Issue(severity="info", message=f"{len(changefreqs)}/{len(url_entries)} URLs have <changefreq>"))
        if priorities:
            issues.append(Issue(severity="info", message=f"{len(priorities)}/{len(url_entries)} URLs have <priority>"))

        # --- Validate same-domain URLs ---
        cross_domain = 0
        for loc in all_locs[:MAX_URLS_TO_PARSE]:
            if loc and not loc.startswith(base):
                cross_domain += 1
        if cross_domain:
            issues.append(Issue(severity="warning", message=f"{cross_domain} URL(s) point to a different domain"))
            score -= 10
    else:
        issues.append(Issue(severity="warning", message="Sitemap exists but contains no URL entries"))
        score -= 15
        all_locs = []

    # --- Check if current URL is in sitemap ---
    normalized = [l.rstrip("/") for l in all_locs]
    if page.url in all_locs or page.url.rstrip("/") in normalized:
        issues.append(Issue(severity="pass", message="Current URL found in sitemap"))
    else:
        issues.append(Issue(severity="info", message="Current URL not found in sitemap"))

    return CategoryResult(name="sitemap", score=max(0, score), issues=issues)
