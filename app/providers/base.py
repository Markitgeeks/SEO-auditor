from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

import certifi
import requests

from app.config import EXTERNAL_API_TIMEOUT


class ProviderError(Exception):
    """Raised when an external provider API call fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class BaseProvider(ABC):
    """Abstract interface for external intelligence providers."""

    def __init__(self, api_key: str, timeout: int = EXTERNAL_API_TIMEOUT):
        self.api_key = api_key
        self.timeout = timeout
        self._session = requests.Session()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    @abstractmethod
    def fetch_domain_data(self, domain: str) -> dict[str, Any]:
        """Fetch all intelligence data for a domain. Returns raw API data."""
        ...

    def _get(self, url: str, params: Optional[dict] = None) -> Any:
        """Make a GET request with standard error handling."""
        try:
            resp = self._session.get(
                url,
                params=params,
                timeout=self.timeout,
                headers=self._headers(),
                verify=certifi.where(),
            )
        except requests.Timeout:
            raise ProviderError(f"API timeout after {self.timeout}s")
        except requests.ConnectionError as e:
            raise ProviderError(f"Connection error: {e}")

        if resp.status_code == 401:
            raise ProviderError("Invalid API key (401)", status_code=401)
        if resp.status_code == 403:
            raise ProviderError("Access denied (403)", status_code=403)
        if resp.status_code == 429:
            raise ProviderError("Rate limit exceeded (429)", status_code=429)
        if resp.status_code >= 400:
            raise ProviderError(
                f"API error {resp.status_code}: {resp.text[:200]}",
                status_code=resp.status_code,
            )
        return resp

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json"}
