"""In-process rate limiting primitives.

Deliberately tiny and dependency-free. KisanProfit runs as a single free-tier
instance, so a per-process sliding window is enough to blunt password guessing,
scripted sign-ups and LLM-quota burn on a publicly linked demo. It is *not* a
distributed limiter: if the service is ever scaled past one instance, move this
to Redis or to the platform's edge (the README's deployment notes say so).

The key table is bounded, so a client sending random `X-Forwarded-For` values
cannot grow memory without limit.
"""
from collections import deque
from time import monotonic

from fastapi import Request

from app.core.config import get_settings

MAX_KEYS = 10_000


class SlidingWindow:
    """Counts attempts per key inside a rolling window."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = max(int(limit), 1)
        self.window = max(int(window_seconds), 1)
        self._hits: dict[str, deque[float]] = {}

    def hit(self, key: str) -> tuple[bool, float]:
        """Record an attempt. Returns (allowed, retry_after_seconds)."""
        now = monotonic()
        cutoff = now - self.window
        bucket = self._hits.get(key)
        if bucket is None:
            if len(self._hits) >= MAX_KEYS:
                # Oldest key out; bounded memory beats perfect fairness here.
                self._hits.pop(next(iter(self._hits)))
            bucket = self._hits[key] = deque()
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False, max(bucket[0] + self.window - now, 0.0)
        bucket.append(now)
        return True, 0.0

    def reset(self) -> None:
        self._hits.clear()


_windows: dict[str, SlidingWindow] = {}


def window(name: str, limit: int) -> SlidingWindow:
    """Cached limiter for a named bucket; rebuilt when the limit changes."""
    current = _windows.get(name)
    if current is None or current.limit != int(limit):
        current = _windows[name] = SlidingWindow(limit, get_settings().RATE_LIMIT_WINDOW_SECONDS)
    return current


def reset_limiters() -> None:
    """Drop all buckets — used between tests so state can't leak."""
    _windows.clear()


def enabled() -> bool:
    return get_settings().RATE_LIMIT_ENABLED.lower() in ("1", "true", "yes")


def client_ip(request: Request) -> str:
    """Caller's IP, honouring the platform proxy's X-Forwarded-For when trusted.

    Exactly one proxy hop is assumed (Render's edge, or the bundled nginx).
    Proxies *append* to X-Forwarded-For rather than replacing it, so a client
    that sends the header itself ends up on the left and the proxy's real peer
    address on the right — hence the rightmost entry. Reading the leftmost
    would let anyone mint a fresh rate-limit budget per request by rotating a
    header, which is the whole point of the limit.
    """
    settings = get_settings()
    if settings.TRUST_PROXY_HEADERS.lower() in ("1", "true", "yes"):
        forwarded = request.headers.get("x-forwarded-for", "")
        hops = [hop.strip() for hop in forwarded.split(",") if hop.strip()]
        if hops:
            return hops[-1]
    return request.client.host if request.client else "unknown"
