from pydantic import BaseModel, HttpUrl
from typing import Any, Literal, Optional

from app.external_models import ExternalInsights


class AuditRequest(BaseModel):
    url: HttpUrl
    include_external: bool = False
    external_modules: Optional[list[str]] = None  # ["similarweb", "semrush"]
    include_crawl: bool = False
    crawl_max_pages: int = 10


class Issue(BaseModel):
    severity: Literal["error", "warning", "info", "pass"]
    message: str
    impact: Optional[str] = None           # "high" / "medium" / "low"
    recommendation: Optional[str] = None
    evidence: Optional[str] = None         # escaped snippet/URL


class IssueSummary(BaseModel):
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    pass_count: int = 0


class CategoryResult(BaseModel):
    name: str
    score: int
    issues: list[Issue]
    metrics: Optional[dict[str, Any]] = None
    summary: Optional[IssueSummary] = None
    duration_ms: Optional[int] = None
    status: str = "ok"           # "ok" | "error"
    error_message: Optional[str] = None


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


class AuditResponse(BaseModel):
    url: str
    overall_score: int
    categories: list[CategoryResult]
    external_insights: Optional[ExternalInsights] = None
    crawl_results: Optional[CrawlResponse] = None
