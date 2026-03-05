"""Search & Backlink Intelligence analyzer (SEMrush)."""
from __future__ import annotations

from app.cache import intel_cache
from app.config import SEMRUSH_API_KEY
from app.external_models import SemrushInsights
from app.providers.semrush import SemrushProvider, map_semrush_response
from app.providers.base import ProviderError


def analyze_search_intel(domain: str) -> SemrushInsights:
    """Fetch SEMrush data for a domain and return typed insights."""
    if not SEMRUSH_API_KEY:
        return SemrushInsights(status="not_configured", data_source="none")

    # Check cache
    cached = intel_cache.get(domain, "semrush")
    if cached is not None:
        return cached

    provider = SemrushProvider(api_key=SEMRUSH_API_KEY)
    try:
        raw = provider.fetch_domain_data(domain)
        mapped = map_semrush_response(raw)
        insights = SemrushInsights(
            status="ok",
            data_source="semrush_api",
            **mapped,
        )
    except ProviderError as e:
        insights = SemrushInsights(
            status="error",
            data_source="none",
            error_message=str(e),
        )

    intel_cache.set(domain, "semrush", insights)
    return insights
