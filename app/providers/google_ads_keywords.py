"""Google Ads Keyword Planner REST API client.

Uses OAuth2 refresh-token flow via requests (no google-ads library dependency).
"""

from __future__ import annotations

import hashlib
import json
from typing import Optional

import certifi
import requests

from app.cache import intel_cache
from app.config import (
    GOOGLE_ADS_DEVELOPER_TOKEN,
    GOOGLE_ADS_CLIENT_ID,
    GOOGLE_ADS_CLIENT_SECRET,
    GOOGLE_ADS_REFRESH_TOKEN,
    GOOGLE_ADS_LOGIN_CUSTOMER_ID,
    GOOGLE_ADS_CUSTOMER_ID,
    KEYWORD_CACHE_TTL,
    KEYWORD_RPM,
)
from app.rate_limit import rate_limiter

# Configure rate limiter
rate_limiter.configure("google_ads_keywords", KEYWORD_RPM)

TOKEN_URL = "https://oauth2.googleapis.com/token"
ADS_API_BASE = "https://googleads.googleapis.com/v17"


class GoogleAdsKeywordsProvider:
    """REST client for Google Ads Keyword Planner API."""

    def __init__(self):
        self.developer_token = GOOGLE_ADS_DEVELOPER_TOKEN
        self.client_id = GOOGLE_ADS_CLIENT_ID
        self.client_secret = GOOGLE_ADS_CLIENT_SECRET
        self.refresh_token = GOOGLE_ADS_REFRESH_TOKEN
        self.login_customer_id = GOOGLE_ADS_LOGIN_CUSTOMER_ID
        self.customer_id = GOOGLE_ADS_CUSTOMER_ID
        self._access_token: Optional[str] = None

    @property
    def is_configured(self) -> bool:
        return bool(
            self.developer_token
            and self.client_id
            and self.client_secret
            and self.refresh_token
            and self.customer_id
        )

    def _refresh_access_token(self) -> str:
        """Get a fresh access token via OAuth2 refresh flow."""
        resp = requests.post(
            TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=10,
            verify=certifi.where(),
        )
        resp.raise_for_status()
        self._access_token = resp.json()["access_token"]
        return self._access_token

    def _headers(self) -> dict[str, str]:
        if not self._access_token:
            self._refresh_access_token()
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "developer-token": self.developer_token,
            "Content-Type": "application/json",
        }
        if self.login_customer_id:
            headers["login-customer-id"] = self.login_customer_id
        return headers

    def generate_keyword_ideas(
        self,
        url: Optional[str] = None,
        seed_keywords: Optional[list[str]] = None,
        language_code: str = "en",
        geo_target_ids: Optional[list[str]] = None,
        page_size: int = 50,
    ) -> list[dict]:
        """Generate keyword ideas from the Google Ads API.

        Returns list of keyword idea dicts.
        """
        if geo_target_ids is None:
            geo_target_ids = ["2840"]  # US

        # Cache key based on inputs
        cache_input = json.dumps({
            "url": url, "seeds": sorted(seed_keywords or []),
            "lang": language_code, "geo": sorted(geo_target_ids),
        }, sort_keys=True)
        cache_hash = hashlib.md5(cache_input.encode()).hexdigest()[:16]
        cache_key = f"keywords_{cache_hash}"
        cache_domain = url or "keywords"

        cached = intel_cache.get(cache_domain, cache_key)
        if cached is not None:
            return cached

        rate_limiter.wait("google_ads_keywords", timeout=30)

        # Build request body
        body: dict = {
            "pageSize": min(page_size, 100),
            "language": f"languageConstants/{_language_id(language_code)}",
            "geoTargetConstants": [f"geoTargetConstants/{gid}" for gid in geo_target_ids],
            "keywordPlanNetwork": "GOOGLE_SEARCH",
        }

        if url:
            body["urlSeed"] = {"url": url}
        if seed_keywords:
            if url:
                body["keywordAndUrlSeed"] = {
                    "url": url,
                    "keywords": seed_keywords[:10],
                }
                body.pop("urlSeed", None)
            else:
                body["keywordSeed"] = {"keywords": seed_keywords[:10]}

        endpoint = f"{ADS_API_BASE}/customers/{self.customer_id}:generateKeywordIdeas"

        resp = requests.post(
            endpoint,
            headers=self._headers(),
            json=body,
            timeout=20,
            verify=certifi.where(),
        )

        # Retry once on 401 (token expired)
        if resp.status_code == 401:
            self._refresh_access_token()
            resp = requests.post(
                endpoint,
                headers=self._headers(),
                json=body,
                timeout=20,
                verify=certifi.where(),
            )

        resp.raise_for_status()
        data = resp.json()

        ideas = []
        for result in data.get("results", []):
            metrics = result.get("keywordIdeaMetrics", {})
            ideas.append({
                "keyword": result.get("text", ""),
                "avg_monthly_searches": metrics.get("avgMonthlySearches"),
                "competition": metrics.get("competition"),
                "competition_index": metrics.get("competitionIndex"),
                "low_cpc_micros": metrics.get("lowTopOfPageBidMicros"),
                "high_cpc_micros": metrics.get("highTopOfPageBidMicros"),
            })

        # Cache result
        intel_cache.set(cache_domain, cache_key, ideas)

        return ideas


def _language_id(code: str) -> str:
    """Map language code to Google Ads language constant ID."""
    lang_map = {
        "en": "1000", "es": "1003", "fr": "1002", "de": "1001",
        "it": "1004", "pt": "1014", "nl": "1010", "ja": "1005",
        "ko": "1012", "zh": "1017", "ru": "1031", "ar": "1019",
        "hi": "1023", "sv": "1015", "no": "1013", "da": "1009",
        "fi": "1011", "pl": "1030", "tr": "1037", "th": "1044",
    }
    return lang_map.get(code, "1000")


# Singleton
google_ads_provider = GoogleAdsKeywordsProvider()
