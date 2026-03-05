"""Traffic & Audience Intelligence analyzer (Similarweb)."""
from __future__ import annotations

from app.cache import intel_cache
from app.config import SIMILARWEB_API_KEY
from app.external_models import SimilarwebInsights
from app.providers.similarweb import SimilarwebProvider, map_similarweb_response
from app.providers.base import ProviderError


def analyze_traffic_intel(domain: str) -> SimilarwebInsights:
    """Fetch Similarweb data for a domain and return typed insights."""
    if not SIMILARWEB_API_KEY:
        return SimilarwebInsights(status="not_configured", data_source="none")

    # Check cache
    cached = intel_cache.get(domain, "similarweb")
    if cached is not None:
        return cached

    provider = SimilarwebProvider(api_key=SIMILARWEB_API_KEY)
    try:
        raw = provider.fetch_domain_data(domain)
        mapped = map_similarweb_response(raw)
        insights = SimilarwebInsights(
            status="ok",
            data_source="similarweb_api",
            **mapped,
        )
    except ProviderError as e:
        insights = SimilarwebInsights(
            status="error",
            data_source="none",
            error_message=str(e),
        )

    intel_cache.set(domain, "similarweb", insights)
    return insights
