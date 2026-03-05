"""Google PageSpeed Insights API client."""

from __future__ import annotations

import certifi
import requests

from app.cache import intel_cache
from app.config import PAGESPEED_API_KEY, PAGESPEED_TIMEOUT, PAGESPEED_CACHE_TTL, PAGESPEED_RPM
from app.rate_limit import rate_limiter

# Configure rate limiter
rate_limiter.configure("pagespeed", PAGESPEED_RPM)

PSI_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


class PageSpeedProvider:
    """Client for the Google PageSpeed Insights API."""

    def __init__(self, api_key: str = PAGESPEED_API_KEY, timeout: int = PAGESPEED_TIMEOUT):
        self.api_key = api_key
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def run_audit(self, url: str, strategy: str = "mobile") -> dict:
        """Run a PSI audit. Returns raw API response dict.

        Uses caching and rate limiting. strategy is 'mobile' or 'desktop'.
        """
        cache_key = f"psi_{strategy}"
        cached = intel_cache.get(url, cache_key)
        if cached is not None:
            cached["_cached"] = True
            return cached

        rate_limiter.wait("pagespeed", timeout=30)

        params = {
            "url": url,
            "strategy": strategy,
            "category": "performance",
        }
        if self.api_key:
            params["key"] = self.api_key

        resp = requests.get(
            PSI_URL,
            params=params,
            timeout=self.timeout,
            verify=certifi.where(),
        )
        resp.raise_for_status()
        data = resp.json()
        data["_cached"] = False

        # Cache with custom TTL (use default cache, key includes strategy)
        intel_cache.set(url, cache_key, data)

        return data


# Module-level singleton
psi_provider = PageSpeedProvider()
