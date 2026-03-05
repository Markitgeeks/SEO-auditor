"""Brand enrichment providers — manual and API-based."""

from app.providers.enrichment.base import BaseEnrichmentProvider, EnrichmentResult
from app.providers.enrichment.manual import ManualEnrichmentProvider
from app.providers.enrichment.auto_fetch import AutoFetchEnrichmentProvider

__all__ = [
    "BaseEnrichmentProvider",
    "EnrichmentResult",
    "ManualEnrichmentProvider",
    "AutoFetchEnrichmentProvider",
]
