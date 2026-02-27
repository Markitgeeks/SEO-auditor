from pydantic import BaseModel, HttpUrl
from typing import Literal


class AuditRequest(BaseModel):
    url: HttpUrl


class Issue(BaseModel):
    severity: Literal["error", "warning", "info", "pass"]
    message: str


class CategoryResult(BaseModel):
    name: str
    score: int
    issues: list[Issue]


class AuditResponse(BaseModel):
    url: str
    overall_score: int
    categories: list[CategoryResult]


# --- Crawl models ---

class CrawlRequest(BaseModel):
    url: HttpUrl
    max_pages: int = 20


class CrawlPageSummary(BaseModel):
    url: str
    title: str
    description: str
    status_code: int
    internal_links: int
    depth: int


class CrawlBrokenLink(BaseModel):
    source_url: str
    target_url: str
    status_code: int


class CrawlDuplicate(BaseModel):
    value: str
    pages: list[str]


class CrawlResponse(BaseModel):
    url: str
    pages_crawled: int
    max_depth: int
    pages: list[CrawlPageSummary]
    broken_links: list[CrawlBrokenLink]
    orphan_pages: list[str]
    duplicate_titles: list[CrawlDuplicate]
    duplicate_descriptions: list[CrawlDuplicate]
    score: int
    issues: list[Issue]
