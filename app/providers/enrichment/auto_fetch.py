"""Auto-fetch enrichment provider — extracts metadata from a domain's homepage."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional
from urllib.parse import urljoin

from app.providers.enrichment.base import BaseEnrichmentProvider, EnrichmentResult

logger = logging.getLogger(__name__)


class AutoFetchEnrichmentProvider(BaseEnrichmentProvider):
    """Fetches homepage HTML and extracts brand-relevant metadata."""

    @property
    def source_name(self) -> str:
        return "auto_fetch"

    def enrich(self, domain: str, existing: Optional[dict[str, Any]] = None) -> EnrichmentResult:
        existing = existing or {}
        fields: dict[str, Any] = {}
        confidence: dict[str, float] = {}
        meta: dict[str, Any] = {}

        try:
            from app.fetcher import fetch_page

            url = f"https://{domain}"
            result = fetch_page(url)
            soup = result.soup

            # --- Extract description (priority: og:description > meta description > title) ---
            og_desc = None
            og_tag = soup.find("meta", attrs={"property": "og:description"})
            if og_tag and og_tag.get("content"):
                og_desc = og_tag["content"].strip()

            meta_desc = None
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag and meta_tag.get("content"):
                meta_desc = meta_tag["content"].strip()

            title_text = None
            title_tag = soup.find("title")
            if title_tag and title_tag.string:
                title_text = title_tag.string.strip()

            # Always auto-fill description
            best_desc = og_desc or meta_desc or title_text
            if best_desc:
                fields["description"] = best_desc[:500]
                confidence["description"] = 0.8 if og_desc else (0.7 if meta_desc else 0.6)

            # --- Favicon ---
            favicon_url = None
            for rel in (["icon"], ["shortcut", "icon"], ["apple-touch-icon"]):
                link = soup.find("link", rel=rel)
                if link and link.get("href"):
                    favicon_url = urljoin(url, link["href"])
                    break
            if favicon_url:
                meta["favicon_url"] = favicon_url

            # --- Theme color ---
            theme_tag = soup.find("meta", attrs={"name": "theme-color"})
            if theme_tag and theme_tag.get("content"):
                meta["theme_color"] = theme_tag["content"].strip()

            # --- Schema.org JSON-LD: infer industry + extra data ---
            ld_items = []
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    ld = json.loads(script.string or "")
                    items = ld if isinstance(ld, list) else [ld]
                    ld_items.extend(items)
                except (json.JSONDecodeError, AttributeError):
                    continue

            for item in ld_items:
                schema_type = item.get("@type", "")
                # Industry from schema type
                if "industry" not in fields:
                    industry = _infer_industry(schema_type)
                    if industry:
                        fields["industry"] = industry
                        confidence["industry"] = 0.7

                # Description from schema if we don't have one yet
                if "description" not in fields and item.get("description"):
                    fields["description"] = str(item["description"])[:500]
                    confidence["description"] = 0.75

            # --- Fallback industry detection from keywords in page text ---
            if "industry" not in fields:
                page_text = (soup.get_text(" ", strip=True) or "").lower()[:5000]
                industry = _infer_industry_from_text(page_text)
                if industry:
                    fields["industry"] = industry
                    confidence["industry"] = 0.5

            # --- OG title / page title ---
            og_title_tag = soup.find("meta", attrs={"property": "og:title"})
            if og_title_tag and og_title_tag.get("content"):
                meta["og_title"] = og_title_tag["content"].strip()
            if title_text:
                meta["page_title"] = title_text

            # --- Keywords meta tag ---
            kw_tag = soup.find("meta", attrs={"name": "keywords"})
            if kw_tag and kw_tag.get("content"):
                meta["keywords"] = kw_tag["content"].strip()

            # Store meta alongside fields
            if meta:
                fields["_meta"] = meta

            return EnrichmentResult(
                status="ok",
                data_source="auto_fetch",
                fields=fields,
                confidence=confidence,
            )

        except Exception as exc:
            logger.warning("Auto-fetch enrichment failed for %s: %s", domain, exc)
            return EnrichmentResult(
                status="error",
                data_source="auto_fetch",
                error_message=str(exc)[:300],
            )


_SCHEMA_INDUSTRY_MAP: dict[str, str] = {
    "Store": "E-commerce",
    "OnlineStore": "E-commerce",
    "Product": "E-commerce",
    "Restaurant": "Food & Beverage",
    "FoodEstablishment": "Food & Beverage",
    "CafeOrCoffeeShop": "Food & Beverage",
    "MedicalBusiness": "Healthcare",
    "Hospital": "Healthcare",
    "Physician": "Healthcare",
    "Dentist": "Healthcare",
    "Pharmacy": "Healthcare",
    "EducationalOrganization": "Education",
    "School": "Education",
    "University": "Education",
    "Course": "Education",
    "RealEstateAgent": "Real Estate",
    "RealEstateListing": "Real Estate",
    "FinancialService": "Finance",
    "BankOrCreditUnion": "Finance",
    "InsuranceAgency": "Insurance",
    "LegalService": "Legal",
    "Attorney": "Legal",
    "TravelAgency": "Travel",
    "Hotel": "Travel & Hospitality",
    "LodgingBusiness": "Travel & Hospitality",
    "SoftwareApplication": "Technology",
    "WebApplication": "Technology",
    "Organization": None,  # too generic
    "AutoDealer": "Automotive",
    "AutoRepair": "Automotive",
    "SportsOrganization": "Sports",
    "FitnessCenter": "Fitness",
    "BeautySalon": "Beauty",
    "HairSalon": "Beauty",
    "EntertainmentBusiness": "Entertainment",
    "NewsArticle": "Media & Publishing",
    "NewsMediaOrganization": "Media & Publishing",
    "GovernmentOrganization": "Government",
    "NGO": "Non-Profit",
    "Church": "Religious",
    "ProfessionalService": "Professional Services",
}

# Keyword patterns for fallback industry detection
_INDUSTRY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("E-commerce", ["shop", "store", "buy now", "add to cart", "checkout", "free shipping", "product"]),
    ("Technology", ["software", "saas", "api", "platform", "developer", "cloud", "ai ", "machine learning"]),
    ("Healthcare", ["health", "medical", "doctor", "patient", "clinic", "hospital", "wellness"]),
    ("Finance", ["financial", "banking", "investment", "insurance", "mortgage", "loan", "credit"]),
    ("Education", ["learn", "course", "student", "university", "school", "training", "certification"]),
    ("Real Estate", ["real estate", "property", "listing", "apartment", "rental", "home for sale"]),
    ("Food & Beverage", ["restaurant", "menu", "delivery", "food", "catering", "dining"]),
    ("Travel & Hospitality", ["hotel", "booking", "travel", "flight", "vacation", "resort"]),
    ("Legal", ["law firm", "attorney", "legal", "lawyer"]),
    ("Automotive", ["automotive", "car dealer", "vehicle", "auto repair"]),
    ("Beauty", ["beauty", "salon", "spa", "skincare", "cosmetic"]),
    ("Fitness", ["fitness", "gym", "workout", "training", "exercise"]),
    ("Media & Publishing", ["news", "magazine", "blog", "publish", "editorial"]),
    ("Non-Profit", ["donate", "nonprofit", "charity", "volunteer", "foundation"]),
    ("Professional Services", ["consulting", "agency", "marketing agency", "accounting"]),
]


def _infer_industry(schema_type: str) -> Optional[str]:
    if not schema_type:
        return None
    if isinstance(schema_type, list):
        for t in schema_type:
            result = _SCHEMA_INDUSTRY_MAP.get(t)
            if result:
                return result
        return None
    return _SCHEMA_INDUSTRY_MAP.get(schema_type)


def _infer_industry_from_text(text: str) -> Optional[str]:
    """Simple keyword-frequency industry detection from page text."""
    best_industry = None
    best_count = 0
    for industry, keywords in _INDUSTRY_KEYWORDS:
        count = sum(1 for kw in keywords if kw in text)
        if count > best_count and count >= 2:
            best_count = count
            best_industry = industry
    return best_industry
