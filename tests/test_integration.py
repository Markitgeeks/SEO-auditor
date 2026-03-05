"""Integration test for /api/audit with mocked external providers."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


class TestAuditEndpoint:
    def test_audit_without_external(self, client):
        """Existing behavior: include_external absent returns no insights."""
        resp = client.post("/api/audit", json={"url": "https://example.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_score" in data
        assert "categories" in data
        assert data.get("external_insights") is None

    @patch("main.analyze_traffic_intel")
    @patch("main.analyze_search_intel")
    def test_audit_with_external_not_configured(self, mock_semrush, mock_sw, client):
        """When API keys are missing, modules return not_configured."""
        from app.external_models import SimilarwebInsights, SemrushInsights
        mock_sw.return_value = SimilarwebInsights(status="not_configured")
        mock_semrush.return_value = SemrushInsights(status="not_configured")

        resp = client.post("/api/audit", json={
            "url": "https://example.com",
            "include_external": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["external_insights"] is not None
        assert data["external_insights"]["similarweb"]["status"] == "not_configured"
        assert data["external_insights"]["semrush"]["status"] == "not_configured"

    @patch("main.analyze_traffic_intel")
    @patch("main.analyze_search_intel")
    def test_audit_with_external_ok(self, mock_semrush, mock_sw, client):
        """When providers return data, insights are included."""
        from app.external_models import SimilarwebInsights, SemrushInsights, Metric
        mock_sw.return_value = SimilarwebInsights(
            status="ok",
            data_source="similarweb_api",
            estimated_monthly_visits=Metric(value=100000, display="100.0K"),
        )
        mock_semrush.return_value = SemrushInsights(
            status="ok",
            data_source="semrush_api",
        )

        resp = client.post("/api/audit", json={
            "url": "https://example.com",
            "include_external": True,
            "external_modules": ["similarweb", "semrush"],
        })
        assert resp.status_code == 200
        data = resp.json()
        sw = data["external_insights"]["similarweb"]
        assert sw["status"] == "ok"
        assert sw["data_source"] == "similarweb_api"
        assert sw["estimated_monthly_visits"]["value"] == 100000

    def test_audit_with_external_selective_module(self, client):
        """Only requested modules are included."""
        with patch("main.analyze_traffic_intel") as mock_sw:
            from app.external_models import SimilarwebInsights
            mock_sw.return_value = SimilarwebInsights(status="not_configured")

            resp = client.post("/api/audit", json={
                "url": "https://example.com",
                "include_external": True,
                "external_modules": ["similarweb"],
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["external_insights"]["similarweb"] is not None
            assert data["external_insights"]["semrush"] is None
