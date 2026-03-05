"""Brand enrichment providers — manual and API-based."""

from app.providers.enrichment.base import BaseEnrichmentProvider, EnrichmentResult
from app.providers.enrichment.manual import ManualEnrichmentProvider

__all__ = [
    "BaseEnrichmentProvider",
    "EnrichmentResult",
    "ManualEnrichmentProvider",
]
