"""Tests for keyword suggestions module."""

from unittest.mock import patch, MagicMock

import pytest

from app.analyzers.keyword_suggestions import get_keyword_suggestions
from app.models import KeywordSuggestResponse


# --- Auth / Privilege Gate Tests ---

@patch("app.analyzers.keyword_suggestions.google_ads_provider")
def test_not_configured(mock_provider):
    mock_provider.is_configured = False
    result = get_keyword_suggestions("https://example.com")
    assert isinstance(result, KeywordSuggestResponse)
    assert result.status == "not_configured"
    assert result.ideas == []


@patch("app.analyzers.keyword_suggestions.google_ads_provider")
def test_configured_success(mock_provider):
    mock_provider.is_configured = True
    mock_provider.generate_keyword_ideas.return_value = [
        {
            "keyword": "seo audit tool",
            "avg_monthly_searches": 1200,
            "competition": "MEDIUM",
            "competition_index": 45,
            "low_cpc_micros": 500000,
            "high_cpc_micros": 1500000,
        },
        {
            "keyword": "website analyzer",
            "avg_monthly_searches": 800,
            "competition": "LOW",
            "competition_index": 20,
            "low_cpc_micros": 300000,
            "high_cpc_micros": 900000,
        },
    ]
    result = get_keyword_suggestions("https://example.com", seed_keywords=["seo"])
    assert result.status == "ok"
    assert result.data_source == "google_ads_keyword_planner"
    assert len(result.ideas) == 2
    assert result.ideas[0].keyword == "seo audit tool"
    assert result.ideas[0].avg_monthly_searches == 1200
    assert result.metrics_summary is not None
    assert result.metrics_summary["total_ideas"] == 2
    assert result.metrics_summary["avg_volume"] == 1000
    assert result.metrics_summary["max_volume"] == 1200


@patch("app.analyzers.keyword_suggestions.google_ads_provider")
def test_api_error(mock_provider):
    mock_provider.is_configured = True
    mock_provider.generate_keyword_ideas.side_effect = Exception("OAuth failed")
    result = get_keyword_suggestions("https://example.com")
    assert result.status == "error"
    assert "OAuth failed" in (result.error_message or "")
    assert result.data_source == "google_ads_keyword_planner"


@patch("app.analyzers.keyword_suggestions.google_ads_provider")
def test_empty_results(mock_provider):
    mock_provider.is_configured = True
    mock_provider.generate_keyword_ideas.return_value = []
    result = get_keyword_suggestions("https://example.com")
    assert result.status == "ok"
    assert len(result.ideas) == 0
    assert result.metrics_summary["total_ideas"] == 0


# --- Endpoint Auth Tests (via FastAPI test client) ---

def test_keywords_status_endpoint():
    """Test GET /api/keywords/status returns enabled status."""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/api/keywords/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "enabled" in data


@patch("main.FEATURE_KEYWORD_PLANNER_ENABLED", False)
def test_keywords_suggest_disabled():
    """Test POST /api/keywords/suggest returns 403 when disabled."""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.post(
        "/api/keywords/suggest",
        json={"url": "https://example.com"},
        headers={"X-Admin-Token": "test-token"},
    )
    assert resp.status_code == 403


@patch("main.FEATURE_KEYWORD_PLANNER_ENABLED", True)
@patch("main.KEYWORD_PLANNER_ADMIN_TOKEN", "correct-token")
def test_keywords_suggest_bad_token():
    """Test POST /api/keywords/suggest returns 403 with wrong token."""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.post(
        "/api/keywords/suggest",
        json={"url": "https://example.com"},
        headers={"X-Admin-Token": "wrong-token"},
    )
    assert resp.status_code == 403
