"""Keyword suggestions module using Google Ads Keyword Planner API."""

from __future__ import annotations

import time
from typing import Optional

from app.models import KeywordIdea, KeywordSuggestResponse
from app.providers.google_ads_keywords import google_ads_provider


def get_keyword_suggestions(
    url: str,
    seed_keywords: Optional[list[str]] = None,
    language_code: str = "en",
    geo_target_ids: Optional[list[str]] = None,
    page_size: int = 50,
) -> KeywordSuggestResponse:
    """Fetch keyword ideas from Google Ads API.

    Returns KeywordSuggestResponse with graceful degradation.
    """
    start = time.perf_counter()

    if not google_ads_provider.is_configured:
        return KeywordSuggestResponse(
            status="not_configured",
            error_message="Google Ads API credentials not configured",
            duration_ms=0,
        )

    try:
        raw_ideas = google_ads_provider.generate_keyword_ideas(
            url=url,
            seed_keywords=seed_keywords or [],
            language_code=language_code,
            geo_target_ids=geo_target_ids,
            page_size=page_size,
        )

        ideas = [KeywordIdea(**idea) for idea in raw_ideas]

        # Build metrics summary
        volumes = [i.avg_monthly_searches for i in ideas if i.avg_monthly_searches is not None]
        comp_indices = [i.competition_index for i in ideas if i.competition_index is not None]

        metrics_summary = {
            "total_ideas": len(ideas),
            "avg_volume": round(sum(volumes) / len(volumes)) if volumes else None,
            "max_volume": max(volumes) if volumes else None,
            "avg_competition_index": round(sum(comp_indices) / len(comp_indices)) if comp_indices else None,
        }

        elapsed = int((time.perf_counter() - start) * 1000)

        return KeywordSuggestResponse(
            status="ok",
            data_source="google_ads_keyword_planner",
            duration_ms=elapsed,
            cached=False,
            ideas=ideas,
            metrics_summary=metrics_summary,
        )

    except Exception as exc:
        elapsed = int((time.perf_counter() - start) * 1000)
        return KeywordSuggestResponse(
            status="error",
            data_source="google_ads_keyword_planner",
            error_message=str(exc)[:200],
            duration_ms=elapsed,
        )
