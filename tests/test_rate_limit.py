import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from app.core.rate_limit import RateLimitExceededError, check_rate_limit, get_redis


@pytest_asyncio.fixture
async def rate_limit_key() -> AsyncGenerator[str]:
    key = f"ratelimit:test:{uuid.uuid4()}"
    yield key
    await get_redis().delete(key)


async def test_allows_requests_under_the_limit(rate_limit_key: str) -> None:
    for _ in range(3):
        await check_rate_limit(rate_limit_key, limit=5, window_seconds=60)


async def test_blocks_requests_over_the_limit(rate_limit_key: str) -> None:
    for _ in range(5):
        await check_rate_limit(rate_limit_key, limit=5, window_seconds=60)

    with pytest.raises(RateLimitExceededError):
        await check_rate_limit(rate_limit_key, limit=5, window_seconds=60)


async def test_resets_after_the_window_expires(rate_limit_key: str) -> None:
    for _ in range(2):
        await check_rate_limit(rate_limit_key, limit=2, window_seconds=1)

    with pytest.raises(RateLimitExceededError):
        await check_rate_limit(rate_limit_key, limit=2, window_seconds=1)

    await asyncio.sleep(1.5)

    await check_rate_limit(rate_limit_key, limit=2, window_seconds=1)


async def test_different_keys_are_independent(rate_limit_key: str) -> None:
    other_key = f"{rate_limit_key}-other"
    try:
        await check_rate_limit(rate_limit_key, limit=1, window_seconds=60)
        # A different key should have its own counter, unaffected by the one above.
        await check_rate_limit(other_key, limit=1, window_seconds=60)
    finally:
        await get_redis().delete(other_key)
