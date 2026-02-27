"""Lightweight BFS web crawler using requests + BeautifulSoup."""

from __future__ import annotations

import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from app.config import CRAWL_DELAY, CRAWL_TIMEOUT, USER_AGENT


@dataclass
class CrawledPage:
    url: str
    title: str = ""
    description: str = ""
    status_code: int = 200
    internal_links: list[str] = field(default_factory=list)
    depth: int = 0


@dataclass
class BrokenLink:
    source_url: str
    target_url: str
    status_code: int


@dataclass
class CrawlResult:
    start_url: str
    pages: list[CrawledPage] = field(default_factory=list)
    broken_links: list[BrokenLink] = field(default_factory=list)
    orphan_pages: list[str] = field(default_factory=list)
    duplicate_titles: dict[str, list[str]] = field(default_factory=dict)
    duplicate_descriptions: dict[str, list[str]] = field(default_factory=dict)
    max_depth: int = 0


def _normalize_url(url: str) -> str:
    """Normalize URL for dedup: strip fragment, trailing slash."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, ""))


def _is_same_domain(url: str, domain: str) -> bool:
    return urlparse(url).netloc == domain


def _extract_page_info(url: str, soup: BeautifulSoup) -> tuple[str, str]:
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag.get("content", "") if desc_tag else ""
    return title, description


def _extract_internal_links(soup: BeautifulSoup, base_url: str, domain: str) -> list[str]:
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(base_url, href)
        if _is_same_domain(full, domain):
            normalized = _normalize_url(full)
            if normalized not in links:
                links.append(normalized)
    return links


def _check_link(url: str) -> tuple[str, int]:
    """HEAD-check a single URL, return (url, status_code)."""
    try:
        resp = requests.head(
            url, headers={"User-Agent": USER_AGENT},
            timeout=CRAWL_TIMEOUT, allow_redirects=True,
        )
        return url, resp.status_code
    except requests.RequestException:
        return url, 0


def crawl_site(start_url: str, max_pages: int = 20) -> CrawlResult:
    """BFS crawl from start_url, limited to max_pages on the same domain."""
    parsed_start = urlparse(start_url)
    domain = parsed_start.netloc
    headers = {"User-Agent": USER_AGENT}

    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque()
    queue.append((_normalize_url(start_url), 0))

    pages: list[CrawledPage] = []
    all_linked: set[str] = set()   # all URLs discovered as link targets
    all_sources: set[str] = set()  # all URLs that were crawled
    link_pairs: list[tuple[str, str]] = []  # (source, target) for broken link checks

    while queue and len(pages) < max_pages:
        url, depth = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = requests.get(url, headers=headers, timeout=CRAWL_TIMEOUT, allow_redirects=True)
        except requests.RequestException:
            continue

        if resp.status_code != 200:
            continue

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            continue

        soup = BeautifulSoup(resp.content, "lxml")
        title, description = _extract_page_info(url, soup)
        internal_links = _extract_internal_links(soup, url, domain)

        page = CrawledPage(
            url=url, title=title, description=description,
            status_code=resp.status_code, internal_links=internal_links, depth=depth,
        )
        pages.append(page)
        all_sources.add(url)

        for link in internal_links:
            all_linked.add(link)
            link_pairs.append((url, link))
            if link not in visited:
                queue.append((link, depth + 1))

        time.sleep(CRAWL_DELAY)

    # --- Post-processing ---

    # Broken link detection via HEAD requests
    external_targets = set()
    for a_src, a_tgt in link_pairs:
        if a_tgt not in all_sources and a_tgt not in external_targets:
            external_targets.add(a_tgt)

    broken_links: list[BrokenLink] = []
    if external_targets:
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(_check_link, list(external_targets)[:50])
            bad_urls = {url: code for url, code in results if code >= 400 or code == 0}

        for src, tgt in link_pairs:
            if tgt in bad_urls:
                broken_links.append(BrokenLink(source_url=src, target_url=tgt, status_code=bad_urls[tgt]))

    # Orphan pages: pages that were crawled but never linked to by other crawled pages
    crawled_urls = {p.url for p in pages}
    orphan_pages = [
        p.url for p in pages
        if p.url != _normalize_url(start_url) and p.url not in all_linked
    ]

    # Duplicate titles
    title_map: dict[str, list[str]] = {}
    for p in pages:
        if p.title:
            title_map.setdefault(p.title, []).append(p.url)
    duplicate_titles = {t: urls for t, urls in title_map.items() if len(urls) > 1}

    # Duplicate descriptions
    desc_map: dict[str, list[str]] = {}
    for p in pages:
        if p.description:
            desc_map.setdefault(p.description, []).append(p.url)
    duplicate_descriptions = {d: urls for d, urls in desc_map.items() if len(urls) > 1}

    max_depth = max((p.depth for p in pages), default=0)

    return CrawlResult(
        start_url=start_url,
        pages=pages,
        broken_links=broken_links,
        orphan_pages=orphan_pages,
        duplicate_titles=duplicate_titles,
        duplicate_descriptions=duplicate_descriptions,
        max_depth=max_depth,
    )
