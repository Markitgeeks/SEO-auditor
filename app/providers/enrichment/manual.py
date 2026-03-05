"""Manual enrichment provider — passes through user-provided brand data.

This is the default enrichment provider that simply validates and
normalizes user-supplied brand profile fields. No external API calls.
"""

from __future__ import annotations

from typing import Any, Optional

from app.providers.enrichment.base import BaseEnrichmentProvider, EnrichmentResult

# Fields that manual enrichment accepts
_ACCEPTED_FIELDS = {
    "industry",
    "description",
    "persona",
    "revenue_range",
    "icp",
    "competitors",
}

_VALID_REVENUE_RANGES = {"<$1M", "$1-5M", "$5-20M", "$20-100M", "$100M+"}


class ManualEnrichmentProvider(BaseEnrichmentProvider):
    """Pass-through provider for user-supplied brand data."""

    @property
    def source_name(self) -> str:
        return "manual"

    def enrich(
        self,
        domain: str,
        existing: Optional[dict[str, Any]] = None,
    ) -> EnrichmentResult:
        existing = existing or {}
        fields: dict[str, Any] = {}
        confidence: dict[str, float] = {}

        for key in _ACCEPTED_FIELDS:
            value = existing.get(key)
            if value is None:
                continue

            # Validate and normalize
            if key == "revenue_range":
                if value not in _VALID_REVENUE_RANGES:
                    continue
            elif key == "competitors":
                if isinstance(value, list):
                    value = [str(v).strip() for v in value if str(v).strip()][:10]
                else:
                    continue
            elif isinstance(value, str):
                value = value.strip()
                if not value:
                    continue
                if len(value) > 500:
                    value = value[:500]

            fields[key] = value
            confidence[key] = 1.0  # User-provided = full confidence

        return EnrichmentResult(
            status="ok",
            data_source="manual",
            fields=fields,
            confidence=confidence,
        )
