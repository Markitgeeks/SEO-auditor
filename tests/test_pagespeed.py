"""Tests for the PageSpeed Insights analyzer."""

from unittest.mock import patch, MagicMock

import pytest

from app.analyzers.pagespeed_insights import _extract_strategy, analyze_pagespeed
from app.models import PageSpeedStrategy


# --- Sample PSI API response ---

MOCK_PSI_RESPONSE = {
    "lighthouseResult": {
        "categories": {
            "performance": {"score": 0.72}
        },
        "audits": {
            "first-contentful-paint": {"numericValue": 1800.5},
            "largest-contentful-paint": {"numericValue": 3200.0},
            "cumulative-layout-shift": {"numericValue": 0.12},
            "total-blocking-time": {"numericValue": 450.0},
            "speed-index": {"numericValue": 2100.0},
            "render-blocking-resources": {
                "score": 0.5,
                "title": "Eliminate render-blocking resources",
                "description": "Reduce blocking scripts",
                "details": {
                    "type": "opportunity",
                    "overallSavingsMs": 320.0,
                },
            },
            "unused-javascript": {
                "score": 0.3,
                "title": "Reduce unused JavaScript",
                "description": "Remove dead code",
                "details": {
                    "type": "opportunity",
                    "overallSavingsMs": 550.0,
                },
            },
            "dom-size": {
                "score": 0.8,
                "title": "Avoid excessive DOM size",
                "description": "Too many nodes",
                "details": {"type": "table"},
            },
        },
    },
    "_cached": False,
}


# --- Extract Strategy Tests ---

def test_extract_strategy_score():
    result = _extract_strategy(MOCK_PSI_RESPONSE)
    assert isinstance(result, PageSpeedStrategy)
    assert result.score == 72


def test_extract_strategy_metrics():
    result = _extract_strategy(MOCK_PSI_RESPONSE)
    assert result.fcp_ms == 1800.5
    assert result.lcp_ms == 3200.0
    assert result.cls == 0.12
    assert result.tbt_ms == 450.0
    assert result.si_ms == 2100.0


def test_extract_strategy_opportunities():
    result = _extract_strategy(MOCK_PSI_RESPONSE)
    assert len(result.opportunities) >= 2
    titles = [o["title"] for o in result.opportunities]
    assert "Reduce unused JavaScript" in titles


def test_extract_strategy_diagnostics():
    result = _extract_strategy(MOCK_PSI_RESPONSE)
    assert len(result.diagnostics) >= 1


def test_extract_empty_response():
    result = _extract_strategy({})
    assert result.score == 0
    assert result.fcp_ms is None


# --- Analyze PSI Tests (mocked) ---

@patch("app.analyzers.pagespeed_insights.psi_provider")
def test_analyze_pagespeed_success(mock_provider):
    mock_provider.run_audit.return_value = MOCK_PSI_RESPONSE
    result = analyze_pagespeed("https://example.com")
    assert result.status == "ok"
    assert result.mobile is not None or result.desktop is not None
    assert result.data_source == "google_pagespeed_insights"
    assert result.duration_ms is not None


@patch("app.analyzers.pagespeed_insights.psi_provider")
def test_analyze_pagespeed_error(mock_provider):
    mock_provider.run_audit.side_effect = Exception("API error")
    result = analyze_pagespeed("https://example.com")
    assert result.status == "error"
    assert "API error" in (result.error_message or "")


@patch("app.analyzers.pagespeed_insights.psi_provider")
def test_analyze_pagespeed_issues(mock_provider):
    mock_provider.run_audit.return_value = MOCK_PSI_RESPONSE
    result = analyze_pagespeed("https://example.com")
    assert len(result.issues) > 0
    severities = [i.severity for i in result.issues]
    assert any(s in severities for s in ["pass", "warning", "error", "info"])


@patch("app.analyzers.pagespeed_insights.psi_provider")
def test_analyze_pagespeed_metrics(mock_provider):
    mock_provider.run_audit.return_value = MOCK_PSI_RESPONSE
    result = analyze_pagespeed("https://example.com")
    assert result.metrics is not None
    # Both mobile and desktop get the same mock, so one should have metrics
    assert "mobile_score" in result.metrics or "desktop_score" in result.metrics
