import time
import threading
from typing import Any, Optional

from app.config import CACHE_TTL_SECONDS, CACHE_MAX_ENTRIES


class TTLCache:
    """Thread-safe in-memory cache with TTL expiration and max entry limit."""

    def __init__(self, ttl: int = CACHE_TTL_SECONDS, max_entries: int = CACHE_MAX_ENTRIES):
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self._ttl = ttl
        self._max = max_entries

    def _make_key(self, domain: str, module: str) -> str:
        return f"{domain}::{module}"

    def get(self, domain: str, module: str) -> Optional[Any]:
        key = self._make_key(domain, module)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            ts, value = entry
            if time.time() - ts > self._ttl:
                del self._store[key]
                return None
            return value

    def set(self, domain: str, module: str, value: Any) -> None:
        key = self._make_key(domain, module)
        with self._lock:
            # Evict expired entries if at capacity
            if len(self._store) >= self._max:
                now = time.time()
                expired = [k for k, (ts, _) in self._store.items() if now - ts > self._ttl]
                for k in expired:
                    del self._store[k]
                # If still full, evict oldest
                if len(self._store) >= self._max:
                    oldest_key = min(self._store, key=lambda k: self._store[k][0])
                    del self._store[oldest_key]
            self._store[key] = (time.time(), value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# Singleton cache instance
intel_cache = TTLCache()
