from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.db.purge_refresh_tokens as purge_module
from app.core.security import hash_password, hash_refresh_token
from app.db.purge_refresh_tokens import main
from app.models import RefreshToken, User
from tests.conftest import async_session_factory as _test_session_factory


async def _make_user(db_session: AsyncSession) -> User:
    user = User(
        name="Yadzael",
        email="purge-test@ch-tech.dev",
        password_hash=hash_password("s3cret-pass"),
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def test_main_purges_tokens_past_retention_and_keeps_the_rest(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    # main() otherwise opens its own session via app.db.session's factory,
    # which points at the real app database, not this test's — see
    # tests/conftest.py for why those must never be the same database.
    monkeypatch.setattr(purge_module, "async_session_factory", _test_session_factory)

    user = await _make_user(db_session)
    now = datetime.now(UTC)
    db_session.add_all(
        [
            RefreshToken(
                user_id=user.id,
                token_hash=hash_refresh_token("long-expired"),
                issued_at=now - timedelta(days=40),
                expires_at=now - timedelta(days=33),
            ),
            RefreshToken(
                user_id=user.id,
                token_hash=hash_refresh_token("still-active"),
                issued_at=now,
                expires_at=now + timedelta(days=7),
            ),
        ]
    )
    await db_session.commit()

    deleted = await main()

    assert deleted == 1
    remaining = await db_session.execute(select(RefreshToken.token_hash))
    assert {row[0] for row in remaining.all()} == {hash_refresh_token("still-active")}
