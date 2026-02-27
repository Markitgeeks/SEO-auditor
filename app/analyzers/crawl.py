"""Crawl results analyzer — scores site-wide crawl findings."""

from __future__ import annotations

from app.models import CategoryResult, Issue
from app.crawler import CrawlResult


def analyze_crawl(result: CrawlResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100

    pages_count = len(result.pages)
    issues.append(Issue(severity="info", message=f"Crawled {pages_count} page(s), max depth {result.max_depth}"))

    # Broken links: -5 each, max -30
    broken = len(result.broken_links)
    if broken:
        penalty = min(broken * 5, 30)
        score -= penalty
        issues.append(Issue(severity="error", message=f"{broken} broken link(s) detected"))
        for bl in result.broken_links[:10]:
            issues.append(Issue(
                severity="error",
                message=f"Broken: {bl.target_url} (status {bl.status_code}) linked from {bl.source_url}"
            ))
    else:
        issues.append(Issue(severity="pass", message="No broken links found"))

    # Orphan pages: -3 each, max -15
    orphans = len(result.orphan_pages)
    if orphans:
        penalty = min(orphans * 3, 15)
        score -= penalty
        issues.append(Issue(severity="warning", message=f"{orphans} orphan page(s) with no internal links pointing to them"))
        for url in result.orphan_pages[:5]:
            issues.append(Issue(severity="warning", message=f"Orphan: {url}"))
    else:
        issues.append(Issue(severity="pass", message="No orphan pages detected"))

    # Duplicate titles: -5 each, max -20
    dup_titles = len(result.duplicate_titles)
    if dup_titles:
        penalty = min(dup_titles * 5, 20)
        score -= penalty
        issues.append(Issue(severity="warning", message=f"{dup_titles} duplicate title(s) found"))
        for title, urls in list(result.duplicate_titles.items())[:5]:
            issues.append(Issue(
                severity="warning",
                message=f"Duplicate title \"{title[:60]}\" on {len(urls)} pages"
            ))
    else:
        issues.append(Issue(severity="pass", message="No duplicate titles"))

    # Duplicate descriptions: -3 each, max -15
    dup_descs = len(result.duplicate_descriptions)
    if dup_descs:
        penalty = min(dup_descs * 3, 15)
        score -= penalty
        issues.append(Issue(severity="warning", message=f"{dup_descs} duplicate meta description(s) found"))
        for desc, urls in list(result.duplicate_descriptions.items())[:5]:
            issues.append(Issue(
                severity="warning",
                message=f"Duplicate description \"{desc[:50]}...\" on {len(urls)} pages"
            ))
    else:
        issues.append(Issue(severity="pass", message="No duplicate meta descriptions"))

    # Crawl depth > 5: -15
    if result.max_depth > 5:
        score -= 15
        issues.append(Issue(
            severity="warning",
            message=f"Max crawl depth is {result.max_depth} -- pages deeper than 5 clicks are hard to discover"
        ))
    else:
        issues.append(Issue(severity="pass", message=f"Crawl depth ({result.max_depth}) is within recommended range"))

    return CategoryResult(name="crawl", score=max(0, min(100, score)), issues=issues)
