"""Base class for brand enrichment providers.

Enrichment providers fill in brand profile fields (industry, persona,
revenue range, description) from either manual input or external APIs.
All providers degrade gracefully — returning status="not_configured"
when credentials are missing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class EnrichmentResult:
    """Standardized output from any enrichment provider."""

    status: str = "ok"  # ok | not_configured | error
    data_source: str = "none"
    error_message: Optional[str] = None
    fields: dict[str, Any] = field(default_factory=dict)
    confidence: dict[str, float] = field(default_factory=dict)  # field → 0.0-1.0


class BaseEnrichmentProvider(ABC):
    """Abstract enrichment provider interface."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable source name (e.g. 'manual', 'clearbit')."""
        ...

    @property
    def is_configured(self) -> bool:
        """Override in subclasses that need API keys."""
        return True

    @abstractmethod
    def enrich(
        self,
        domain: str,
        existing: Optional[dict[str, Any]] = None,
    ) -> EnrichmentResult:
        """Enrich a brand profile for the given domain.

        Args:
            domain: The brand's primary domain.
            existing: Current brand profile fields (to avoid overwriting
                      user-provided data with lower-confidence API data).

        Returns:
            EnrichmentResult with populated fields dict.
        """
        ...
