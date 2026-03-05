"""Google PageSpeed Insights API client."""

from __future__ import annotations

import time

import certifi
import requests

from app.cache import intel_cache
from app.config import PAGESPEED_API_KEY, PAGESPEED_TIMEOUT, PAGESPEED_CACHE_TTL, PAGESPEED_RPM
from app.rate_limit import rate_limiter

# Without an API key the public PSI endpoint allows ~1 req/sec.
# With a key it's ~400 req/100s. Adjust local limiter accordingly.
_effective_rpm = PAGESPEED_RPM if PAGESPEED_API_KEY else 25
rate_limiter.configure("pagespeed", _effective_rpm)

PSI_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

MAX_RETRIES = 3
BACKOFF_SECONDS = [5, 15, 30]  # wait before each retry


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

        Uses caching, rate limiting, and retry with exponential backoff on 429.
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

        last_err = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(
                    PSI_URL,
                    params=params,
                    timeout=self.timeout,
                    verify=certifi.where(),
                )
                if resp.status_code == 429:
                    wait = BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)]
                    # Also check Retry-After header
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait = max(wait, int(retry_after))
                        except ValueError:
                            pass
                    time.sleep(wait)
                    last_err = f"Rate limited (429), retried after {wait}s"
                    continue

                resp.raise_for_status()
                data = resp.json()
                data["_cached"] = False
                intel_cache.set(url, cache_key, data)
                return data

            except requests.exceptions.HTTPError as e:
                if "429" in str(e):
                    wait = BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)]
                    time.sleep(wait)
                    last_err = str(e)
                    continue
                raise
            except requests.exceptions.Timeout:
                last_err = f"Timeout after {self.timeout}s"
                continue

        raise RuntimeError(
            f"PSI {strategy} failed after {MAX_RETRIES} attempts: {last_err}"
        )


# Module-level singleton
psi_provider = PageSpeedProvider()
