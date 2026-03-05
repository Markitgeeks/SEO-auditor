from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel


# --- Shared sub-models ---

class Metric(BaseModel):
    value: Optional[float] = None
    display: str = "N/A"


class ChannelShare(BaseModel):
    channel: str  # direct, search, social, referrals, email, display
    share: float  # 0.0 – 1.0


class CountryShare(BaseModel):
    country: str  # ISO-3166-1 alpha-2 or name
    share: float


class ReferringSite(BaseModel):
    domain: str
    share: Optional[float] = None


class CompetitorDomain(BaseModel):
    domain: str
    affinity: Optional[float] = None


class KeywordRow(BaseModel):
    keyword: str
    position: Optional[int] = None
    url: Optional[str] = None
    volume: Optional[int] = None


class KeywordBucket(BaseModel):
    range: str  # "1-3", "4-10", "11-20", "21-100"
    count: int


class BacklinkRow(BaseModel):
    source_url: str
    target_url: Optional[str] = None
    anchor: Optional[str] = None


class BacklinkSummary(BaseModel):
    total_backlinks: Optional[int] = None
    referring_domains: Optional[int] = None
    follow_count: Optional[int] = None
    nofollow_count: Optional[int] = None


# --- Similarweb Insights ---

StatusType = Literal["ok", "not_configured", "error"]
DataSourceType = Literal["similarweb_api", "none"]


class SimilarwebInsights(BaseModel):
    status: StatusType = "not_configured"
    data_source: DataSourceType = "none"
    error_message: Optional[str] = None

    estimated_monthly_visits: Metric = Metric()
    visit_duration: Metric = Metric()
    pages_per_visit: Metric = Metric()
    bounce_rate: Metric = Metric()

    traffic_channels: list[ChannelShare] = []
    top_countries: list[CountryShare] = []
    top_referring_sites: list[ReferringSite] = []
    top_destination_sites: list[ReferringSite] = []
    similar_sites: list[CompetitorDomain] = []


# --- SEMrush Insights ---

SemrushDataSource = Literal["semrush_api", "none"]


class SemrushInsights(BaseModel):
    status: StatusType = "not_configured"
    data_source: SemrushDataSource = "none"
    error_message: Optional[str] = None

    organic_keywords: list[KeywordRow] = []
    keyword_distribution: list[KeywordBucket] = []
    estimated_organic_traffic: Metric = Metric()

    backlink_summary: BacklinkSummary = BacklinkSummary()
    top_backlinks: list[BacklinkRow] = []
    top_referring_domains: list[ReferringSite] = []
    organic_competitors: list[CompetitorDomain] = []


# --- Combined ---

class ExternalInsights(BaseModel):
    similarweb: Optional[SimilarwebInsights] = None
    semrush: Optional[SemrushInsights] = None
