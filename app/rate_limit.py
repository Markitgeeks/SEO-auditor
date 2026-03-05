"""Token-bucket rate limiter keyed by module name."""

import time
import threading


class RateLimiter:
    """Thread-safe token-bucket rate limiter.

    Each module gets its own bucket with a configurable tokens-per-minute rate.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # module -> {tokens, last_refill, rpm}
        self._buckets: dict[str, dict] = {}

    def configure(self, module: str, tokens_per_minute: int) -> None:
        with self._lock:
            self._buckets[module] = {
                "tokens": tokens_per_minute,
                "last_refill": time.monotonic(),
                "rpm": tokens_per_minute,
            }

    def _refill(self, bucket: dict) -> None:
        now = time.monotonic()
        elapsed = now - bucket["last_refill"]
        refill = elapsed * (bucket["rpm"] / 60.0)
        if refill > 0:
            bucket["tokens"] = min(bucket["rpm"], bucket["tokens"] + refill)
            bucket["last_refill"] = now

    def allow(self, module: str) -> bool:
        with self._lock:
            bucket = self._buckets.get(module)
            if bucket is None:
                return True
            self._refill(bucket)
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True
            return False

    def wait(self, module: str, timeout: float = 30.0) -> bool:
        """Block until a token is available. Returns False on timeout."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.allow(module):
                return True
            time.sleep(0.1)
        return False


# Singleton
rate_limiter = RateLimiter()
