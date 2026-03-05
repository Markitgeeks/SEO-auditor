"""Tests for provider clients with mocked HTTP responses."""
import json
import pytest
from unittest.mock import patch, MagicMock

from app.providers.similarweb import SimilarwebProvider, map_similarweb_response
from app.providers.semrush import SemrushProvider, map_semrush_response
from app.providers.base import ProviderError


class TestSimilarwebProvider:
    def _mock_response(self, json_data, status_code=200):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data
        resp.text = json.dumps(json_data)
        return resp

    @patch("app.providers.base.requests.Session.get")
    def test_fetch_returns_data(self, mock_get):
        mock_get.return_value = self._mock_response({"visits": [{"visits": 50000}]})
        provider = SimilarwebProvider(api_key="test-key")
        data = provider.fetch_domain_data("example.com")
        assert "total_visits" in data
        assert mock_get.call_count >= 1

    @patch("app.providers.base.requests.Session.get")
    def test_401_raises(self, mock_get):
        resp = self._mock_response({}, 401)
        mock_get.return_value = resp
        provider = SimilarwebProvider(api_key="bad-key")
        # Individual endpoints catch ProviderError, so data still comes back
        data = provider.fetch_domain_data("example.com")
        assert len(data.get("_errors", [])) > 0

    def test_not_configured(self):
        provider = SimilarwebProvider(api_key="")
        assert provider.is_configured is False


class TestSemrushProvider:
    @patch("app.providers.base.requests.Session.get")
    def test_fetch_returns_data(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "Ph;Po;Ur;Nq;Td\nseo tools;5;https://example.com;12000;0.5\n"
        mock_get.return_value = resp
        provider = SemrushProvider(api_key="test-key")
        data = provider.fetch_domain_data("example.com")
        assert "organic_keywords" in data

    @patch("app.providers.base.requests.Session.get")
    def test_error_response(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "ERROR 50 :: NOTHING FOUND"
        mock_get.return_value = resp
        provider = SemrushProvider(api_key="test-key")
        data = provider.fetch_domain_data("example.com")
        assert len(data.get("_errors", [])) > 0


class TestMapSimilarweb:
    def test_maps_visits(self):
        raw = {"total_visits": {"visits": [{"visits": 123456}]}}
        result = map_similarweb_response(raw)
        assert result["estimated_monthly_visits"]["value"] == 123456.0

    def test_maps_traffic_channels(self):
        raw = {"traffic_sources": {"overview": {"Direct": 0.4, "Search": 0.3}}}
        result = map_similarweb_response(raw)
        channels = result.get("traffic_channels", [])
        assert len(channels) >= 2

    def test_empty_raw(self):
        result = map_similarweb_response({})
        assert result == {}


class TestMapSemrush:
    def test_maps_keywords(self):
        raw = {
            "organic_keywords": [
                {"Ph": "seo", "Po": "3", "Ur": "https://x.com", "Nq": "5000", "Td": ""},
                {"Ph": "audit", "Po": "15", "Ur": "https://x.com/a", "Nq": "1000", "Td": ""},
            ]
        }
        result = map_semrush_response(raw)
        assert len(result["organic_keywords"]) == 2
        assert result["keyword_distribution"][0]["range"] == "1-3"
        assert result["keyword_distribution"][0]["count"] == 1

    def test_maps_backlink_summary(self):
        raw = {
            "backlinks_overview": [{"total": "500", "domains_num": "50", "follows_num": "400", "nofollows_num": "100"}]
        }
        result = map_semrush_response(raw)
        assert result["backlink_summary"]["total_backlinks"] == 500

    def test_empty_raw(self):
        result = map_semrush_response({})
        assert "keyword_distribution" in result  # always present
