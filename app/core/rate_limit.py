from collections.abc import Awaitable, Callable
from functools import lru_cache

import redis.asyncio as redis
from fastapi import Request

from app.core.config import get_settings
from app.core.errors import AppError


class RateLimitExceededError(AppError):
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(429, "RATE_LIMIT_EXCEEDED", "Too many requests")


@lru_cache
def get_redis() -> redis.Redis:
    return redis.from_url(get_settings().redis_url, decode_responses=True)


async def check_rate_limit(key: str, *, limit: int, window_seconds: int) -> None:
    """Fixed-window counter (ADR-0007): INCR a key, set its TTL on first hit.

    Raise RateLimitExceededError once `limit` hits land inside one window.
    """
    client = get_redis()
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, window_seconds)

    if count > limit:
        ttl = await client.ttl(key)
        raise RateLimitExceededError(retry_after_seconds=max(ttl, 1))


def ip_rate_limiter(
    *, limit: int, window_seconds: int, scope: str
) -> Callable[[Request], Awaitable[None]]:
    """Dependency factory for per-client-IP limits (e.g. "API Pública": 100
    req/min in API.md) — for routes to opt into once they exist."""

    async def _dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        await check_rate_limit(
            f"ratelimit:{scope}:{client_ip}", limit=limit, window_seconds=window_seconds
        )

    return _dependency
