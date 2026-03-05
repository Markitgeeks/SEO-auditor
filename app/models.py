from pydantic import BaseModel, HttpUrl
from typing import Any, Literal, Optional

from app.external_models import ExternalInsights


class AuditRequest(BaseModel):
    url: HttpUrl
    include_external: bool = False
    external_modules: Optional[list[str]] = None  # ["similarweb", "semrush"]
    include_crawl: bool = False
    crawl_max_pages: int = 10
    include_pagespeed: bool = False
    include_schema_validation: bool = False


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


# --- PageSpeed Insights models ---

class PageSpeedStrategy(BaseModel):
    score: int = 0
    fcp_ms: Optional[float] = None
    lcp_ms: Optional[float] = None
    cls: Optional[float] = None
    tbt_ms: Optional[float] = None
    si_ms: Optional[float] = None
    opportunities: list[dict] = []
    diagnostics: list[dict] = []


class PageSpeedResult(BaseModel):
    status: str = "not_configured"
    data_source: str = "none"
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    cached: bool = False
    mobile: Optional[PageSpeedStrategy] = None
    desktop: Optional[PageSpeedStrategy] = None
    issues: list[Issue] = []
    metrics: Optional[dict] = None


# --- Schema Validation models ---

class SchemaEntity(BaseModel):
    entity_type: str
    entity_id: Optional[str] = None
    source: str = "jsonld"  # jsonld/microdata/rdfa
    properties_found: list[str] = []
    valid: bool = True


class SchemaValidationResult(BaseModel):
    status: str = "ok"
    data_source: str = "local_schema_validation"
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    entities: list[SchemaEntity] = []
    issues: list[Issue] = []
    metrics: Optional[dict] = None


# --- Keyword Suggestion models ---

class KeywordIdea(BaseModel):
    keyword: str
    avg_monthly_searches: Optional[int] = None
    competition: Optional[str] = None
    competition_index: Optional[int] = None
    low_cpc_micros: Optional[int] = None
    high_cpc_micros: Optional[int] = None


class KeywordSuggestRequest(BaseModel):
    url: HttpUrl
    seed_keywords: list[str] = []
    language_code: str = "en"
    geo_target_ids: list[str] = ["2840"]
    page_size: int = 50


class KeywordSuggestResponse(BaseModel):
    status: str = "not_configured"
    data_source: str = "none"
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    cached: bool = False
    ideas: list[KeywordIdea] = []
    metrics_summary: Optional[dict] = None


class AuditResponse(BaseModel):
    url: str
    overall_score: int
    categories: list[CategoryResult]
    external_insights: Optional[ExternalInsights] = None
    crawl_results: Optional[CrawlResponse] = None
    pagespeed_insights: Optional[PageSpeedResult] = None
    schema_validation: Optional[SchemaValidationResult] = None
