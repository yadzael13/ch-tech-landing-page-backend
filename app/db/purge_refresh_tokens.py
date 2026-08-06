"""Deletes refresh_tokens rows past their retention window.

Nothing else in the app ever removes a row from this table (RefreshToken is
immutable except for revoked_at, DATABASE_SCHEMA.md "refresh_tokens") — left
alone, it grows without bound. Run periodically:

    docker compose exec backend python -m app.db.purge_refresh_tokens

Wire this into a host cron job (ADR-0011 — self-managed EC2, no in-process
scheduler in this stack); it is not, and must not be, called from an HTTP
route.
"""

import asyncio
import logging
from datetime import timedelta

from app.application.use_cases.auth import PurgeExpiredRefreshTokens
from app.core.config import get_settings
from app.db.session import async_session_factory
from app.infrastructure.repositories.refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)

logger = logging.getLogger(__name__)


async def main() -> int:
    settings = get_settings()
    async with async_session_factory() as session:
        use_case = PurgeExpiredRefreshTokens(
            refresh_token_repository=SQLAlchemyRefreshTokenRepository(session),
            retention=timedelta(days=settings.refresh_token_retention_days),
        )
        deleted = await use_case.execute()
    logger.info("Purged %d refresh token(s) past retention", deleted)
    return deleted


if __name__ == "__main__":
    asyncio.run(main())
