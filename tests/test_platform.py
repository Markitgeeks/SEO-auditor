"""Tests for multi-brand platform features: summary, brands, audits, uploads, enrichment."""

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    from app.database import init_db, engine, Base

    # Fresh DB for each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestClient(app)


# ============================================================
# Executive Summary Generator
# ============================================================


class TestExecutiveSummary:
    def test_basic_summary(self):
        from app.summary import generate_executive_summary

        categories = [
            {
                "name": "meta_tags",
                "score": 40,
                "issues": [
                    {"severity": "error", "impact": "high", "message": "Missing title tag", "recommendation": "Add a title tag"},
                    {"severity": "warning", "impact": "medium", "message": "Description too short"},
                    {"severity": "pass", "message": "OG tags present"},
                ],
            },
            {
                "name": "performance",
                "score": 80,
                "issues": [
                    {"severity": "warning", "impact": "medium", "message": "Slow TTFB"},
                ],
            },
        ]
        result = generate_executive_summary(categories, brand_name="Acme", overall_score=60)

        assert result["brand_one_liner"] == "Acme — SEO audit and growth analysis."
        assert result["overall_score"] == 60
        assert len(result["top_opportunities"]) > 0
        assert result["top_opportunities"][0]["severity"] in ("error", "warning")
        assert "pass" not in [o["severity"] for o in result["top_opportunities"]]
        assert "meta_tags" in result["per_category_quick_wins"]
        assert result["sales_narrative"]["whats_holding_growth_back"]

    def test_summary_with_description(self):
        from app.summary import generate_executive_summary

        result = generate_executive_summary(
            [], brand_name="Test", brand_description="A cool brand", overall_score=90
        )
        assert result["brand_one_liner"] == "A cool brand"

    def test_summary_no_issues(self):
        from app.summary import generate_executive_summary

        result = generate_executive_summary(
            [{"name": "meta_tags", "score": 100, "issues": []}],
            overall_score=100,
        )
        assert len(result["top_opportunities"]) == 0

    def test_summary_none_recommendation(self):
        """Regression: recommendation=None should not crash."""
        from app.summary import generate_executive_summary

        categories = [
            {
                "name": "images",
                "score": 50,
                "issues": [
                    {"severity": "error", "impact": "high", "message": "No alt text", "recommendation": None},
                ],
            },
        ]
        result = generate_executive_summary(categories, overall_score=50)
        assert len(result["top_opportunities"]) > 0


# ============================================================
# Brand CRUD
# ============================================================


class TestBrandCRUD:
    def test_create_brand(self, client):
        resp = client.post("/api/brands", json={"name": "Acme", "primary_domain": "acme.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Acme"
        assert data["primary_domain"] == "acme.com"
        assert "id" in data

    def test_list_brands(self, client):
        client.post("/api/brands", json={"name": "A", "primary_domain": "a.com"})
        client.post("/api/brands", json={"name": "B", "primary_domain": "b.com"})
        resp = client.get("/api/brands")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_brand(self, client):
        create_resp = client.post("/api/brands", json={"name": "C", "primary_domain": "c.com"})
        brand_id = create_resp.json()["id"]
        resp = client.get(f"/api/brands/{brand_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "C"

    def test_get_brand_not_found(self, client):
        resp = client.get("/api/brands/nonexistent-id")
        assert resp.status_code == 404

    def test_update_brand(self, client):
        create_resp = client.post("/api/brands", json={"name": "D", "primary_domain": "d.com"})
        brand_id = create_resp.json()["id"]
        resp = client.patch(f"/api/brands/{brand_id}", json={"industry": "Tech", "persona": "CTO"})
        assert resp.status_code == 200
        assert resp.json()["industry"] == "Tech"
        assert resp.json()["persona"] == "CTO"


# ============================================================
# Audit Persistence
# ============================================================


class TestAuditPersistence:
    def test_audit_with_save(self, client):
        # Create brand first
        brand = client.post("/api/brands", json={"name": "E", "primary_domain": "example.com"}).json()
        brand_id = brand["id"]

        # Run audit with save
        resp = client.post("/api/audit", json={
            "url": "https://example.com",
            "brand_id": brand_id,
            "save_result": True,
            "include_exec_summary": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("audit_id") is not None
        assert data.get("executive_summary") is not None

        # Check audit appears in brand's audit list
        audits = client.get(f"/api/brands/{brand_id}/audits").json()
        assert len(audits) == 1
        assert audits[0]["overall_score"] == data["overall_score"]

    def test_audit_without_save(self, client):
        resp = client.post("/api/audit", json={"url": "https://example.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("audit_id") is None

    def test_view_saved_audit(self, client):
        brand = client.post("/api/brands", json={"name": "F", "primary_domain": "example.com"}).json()
        audit_resp = client.post("/api/audit", json={
            "url": "https://example.com",
            "brand_id": brand["id"],
            "save_result": True,
        })
        audit_id = audit_resp.json()["audit_id"]

        detail = client.get(f"/api/audits/{audit_id}")
        assert detail.status_code == 200
        detail_data = detail.json()
        assert detail_data["audited_url"].rstrip("/") == "https://example.com"
        assert "category_results_json" in detail_data


# ============================================================
# Upload Validation
# ============================================================


class TestUploadValidation:
    def test_upload_without_brand(self, client):
        resp = client.post("/api/uploads", files={"file": ("logo.png", b"\x89PNG\r\n", "image/png")})
        # brand_id is optional — upload succeeds without it
        assert resp.status_code == 200

    def test_upload_invalid_mime(self, client):
        brand = client.post("/api/brands", json={"name": "G", "primary_domain": "g.com"}).json()
        resp = client.post(
            f"/api/uploads?brand_id={brand['id']}&file_type=logo",
            files={"file": ("script.js", b"alert(1)", "application/javascript")},
        )
        assert resp.status_code == 400

    def test_upload_valid_image(self, client):
        brand = client.post("/api/brands", json={"name": "H", "primary_domain": "h.com"}).json()
        # Minimal valid PNG header
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        resp = client.post(
            f"/api/uploads?brand_id={brand['id']}&file_type=logo",
            files={"file": ("logo.png", png_data, "image/png")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "filename" in data


# ============================================================
# Enrichment Providers
# ============================================================


class TestManualEnrichment:
    def test_basic_enrichment(self):
        from app.providers.enrichment import ManualEnrichmentProvider

        provider = ManualEnrichmentProvider()
        result = provider.enrich("example.com", existing={
            "industry": "E-commerce",
            "persona": "Marketing Director",
            "revenue_range": "$5-20M",
        })
        assert result.status == "ok"
        assert result.data_source == "manual"
        assert result.fields["industry"] == "E-commerce"
        assert result.fields["persona"] == "Marketing Director"
        assert result.fields["revenue_range"] == "$5-20M"
        assert result.confidence["industry"] == 1.0

    def test_empty_enrichment(self):
        from app.providers.enrichment import ManualEnrichmentProvider

        provider = ManualEnrichmentProvider()
        result = provider.enrich("example.com", existing={})
        assert result.status == "ok"
        assert len(result.fields) == 0

    def test_invalid_revenue_range(self):
        from app.providers.enrichment import ManualEnrichmentProvider

        provider = ManualEnrichmentProvider()
        result = provider.enrich("example.com", existing={"revenue_range": "a billion dollars"})
        assert "revenue_range" not in result.fields

    def test_truncates_long_values(self):
        from app.providers.enrichment import ManualEnrichmentProvider

        provider = ManualEnrichmentProvider()
        result = provider.enrich("example.com", existing={"description": "x" * 1000})
        assert len(result.fields["description"]) == 500

    def test_competitors_list(self):
        from app.providers.enrichment import ManualEnrichmentProvider

        provider = ManualEnrichmentProvider()
        result = provider.enrich("example.com", existing={"competitors": ["a.com", "b.com", ""]})
        assert result.fields["competitors"] == ["a.com", "b.com"]

    def test_source_name(self):
        from app.providers.enrichment import ManualEnrichmentProvider

        assert ManualEnrichmentProvider().source_name == "manual"


class TestEnrichmentBase:
    def test_result_defaults(self):
        from app.providers.enrichment import EnrichmentResult

        r = EnrichmentResult()
        assert r.status == "ok"
        assert r.fields == {}
        assert r.confidence == {}

    def test_not_configured_result(self):
        from app.providers.enrichment import EnrichmentResult

        r = EnrichmentResult(status="not_configured", data_source="clearbit", error_message="No API key")
        assert r.status == "not_configured"
        assert r.error_message == "No API key"


# ============================================================
# PDF Report (branded endpoint)
# ============================================================


class TestBrandedPDF:
    def test_pdf_from_saved_audit(self, client):
        brand = client.post("/api/brands", json={"name": "PDFTest", "primary_domain": "example.com"}).json()
        audit = client.post("/api/audit", json={
            "url": "https://example.com",
            "brand_id": brand["id"],
            "save_result": True,
        }).json()

        resp = client.post("/api/reports/pdf", json={"audit_id": audit["audit_id"]})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert len(resp.content) > 100  # Not empty

    def test_pdf_audit_not_found(self, client):
        resp = client.post("/api/reports/pdf", json={"audit_id": "nonexistent"})
        assert resp.status_code == 404
