import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, hash_refresh_token
from app.infrastructure.repositories.refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)
from app.models import User as UserModel


async def _make_user(db_session: AsyncSession) -> uuid.UUID:
    user = UserModel(
        name="Yadzael",
        email=f"{uuid.uuid4()}@ch-tech.dev",
        password_hash=hash_password("s3cret-pass"),
    )
    db_session.add(user)
    await db_session.flush()
    return user.id


async def test_create_persists_and_returns_the_token(db_session: AsyncSession) -> None:
    user_id = await _make_user(db_session)
    repo = SQLAlchemyRefreshTokenRepository(db_session)
    now = datetime.now(UTC)

    result = await repo.create(
        user_id=user_id,
        token_hash=hash_refresh_token("raw-token"),
        issued_at=now,
        expires_at=now + timedelta(days=7),
        user_agent="pytest",
        ip_address="127.0.0.1",
    )

    assert result.user_id == user_id
    assert result.revoked_at is None


async def test_get_by_token_hash_returns_none_when_missing(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyRefreshTokenRepository(db_session)
    assert await repo.get_by_token_hash("does-not-exist") is None


async def test_get_by_token_hash_returns_the_matching_token(
    db_session: AsyncSession,
) -> None:
    user_id = await _make_user(db_session)
    repo = SQLAlchemyRefreshTokenRepository(db_session)
    now = datetime.now(UTC)
    created = await repo.create(
        user_id=user_id,
        token_hash=hash_refresh_token("raw-token"),
        issued_at=now,
        expires_at=now + timedelta(days=7),
        user_agent=None,
        ip_address=None,
    )

    found = await repo.get_by_token_hash(hash_refresh_token("raw-token"))

    assert found is not None
    assert found.id == created.id


async def test_save_persists_a_revocation(db_session: AsyncSession) -> None:
    user_id = await _make_user(db_session)
    repo = SQLAlchemyRefreshTokenRepository(db_session)
    now = datetime.now(UTC)
    token = await repo.create(
        user_id=user_id,
        token_hash=hash_refresh_token("raw-token"),
        issued_at=now,
        expires_at=now + timedelta(days=7),
        user_agent=None,
        ip_address=None,
    )

    token.revoke(at=now)
    await repo.save(token)

    reloaded = await repo.get_by_token_hash(hash_refresh_token("raw-token"))
    assert reloaded is not None
    assert reloaded.revoked_at is not None


async def test_revoke_if_active_revokes_and_returns_the_token(
    db_session: AsyncSession,
) -> None:
    user_id = await _make_user(db_session)
    repo = SQLAlchemyRefreshTokenRepository(db_session)
    now = datetime.now(UTC)
    created = await repo.create(
        user_id=user_id,
        token_hash=hash_refresh_token("raw-token"),
        issued_at=now,
        expires_at=now + timedelta(days=7),
        user_agent=None,
        ip_address=None,
    )

    revoked = await repo.revoke_if_active(hash_refresh_token("raw-token"), at=now)

    assert revoked is not None
    assert revoked.id == created.id
    assert revoked.revoked_at == now


async def test_revoke_if_active_is_single_use(db_session: AsyncSession) -> None:
    # The atomicity this exists for: two callers racing the same raw token
    # (a retried request, or an attacker replaying a stolen one) must not
    # both be able to treat it as active — only one UPDATE can win the
    # `revoked_at IS NULL` condition.
    user_id = await _make_user(db_session)
    repo = SQLAlchemyRefreshTokenRepository(db_session)
    now = datetime.now(UTC)
    await repo.create(
        user_id=user_id,
        token_hash=hash_refresh_token("raw-token"),
        issued_at=now,
        expires_at=now + timedelta(days=7),
        user_agent=None,
        ip_address=None,
    )

    first = await repo.revoke_if_active(hash_refresh_token("raw-token"), at=now)
    second = await repo.revoke_if_active(hash_refresh_token("raw-token"), at=now)

    assert first is not None
    assert second is None


async def test_revoke_if_active_returns_none_when_expired(
    db_session: AsyncSession,
) -> None:
    user_id = await _make_user(db_session)
    repo = SQLAlchemyRefreshTokenRepository(db_session)
    now = datetime.now(UTC)
    await repo.create(
        user_id=user_id,
        token_hash=hash_refresh_token("raw-token"),
        issued_at=now - timedelta(days=8),
        expires_at=now - timedelta(days=1),
        user_agent=None,
        ip_address=None,
    )

    assert await repo.revoke_if_active(hash_refresh_token("raw-token"), at=now) is None


async def test_revoke_if_active_returns_none_when_missing(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyRefreshTokenRepository(db_session)
    result = await repo.revoke_if_active("does-not-exist", at=datetime.now(UTC))
    assert result is None


async def test_purge_older_than_deletes_long_expired_tokens(
    db_session: AsyncSession,
) -> None:
    user_id = await _make_user(db_session)
    repo = SQLAlchemyRefreshTokenRepository(db_session)
    now = datetime.now(UTC)
    await repo.create(
        user_id=user_id,
        token_hash=hash_refresh_token("long-expired"),
        issued_at=now - timedelta(days=40),
        expires_at=now - timedelta(days=33),
        user_agent=None,
        ip_address=None,
    )

    deleted = await repo.purge_older_than(now - timedelta(days=30))

    assert deleted == 1
    assert await repo.get_by_token_hash(hash_refresh_token("long-expired")) is None


async def test_purge_older_than_deletes_long_revoked_tokens(
    db_session: AsyncSession,
) -> None:
    user_id = await _make_user(db_session)
    repo = SQLAlchemyRefreshTokenRepository(db_session)
    now = datetime.now(UTC)
    created = await repo.create(
        user_id=user_id,
        token_hash=hash_refresh_token("long-revoked"),
        issued_at=now - timedelta(days=40),
        expires_at=now + timedelta(days=7),
        user_agent=None,
        ip_address=None,
    )
    created.revoke(at=now - timedelta(days=31))
    await repo.save(created)

    deleted = await repo.purge_older_than(now - timedelta(days=30))

    assert deleted == 1
    assert await repo.get_by_token_hash(hash_refresh_token("long-revoked")) is None


async def test_purge_older_than_keeps_active_and_recently_revoked_tokens(
    db_session: AsyncSession,
) -> None:
    user_id = await _make_user(db_session)
    repo = SQLAlchemyRefreshTokenRepository(db_session)
    now = datetime.now(UTC)
    await repo.create(
        user_id=user_id,
        token_hash=hash_refresh_token("still-active"),
        issued_at=now,
        expires_at=now + timedelta(days=7),
        user_agent=None,
        ip_address=None,
    )
    recently_revoked = await repo.create(
        user_id=user_id,
        token_hash=hash_refresh_token("recently-revoked"),
        issued_at=now - timedelta(days=2),
        expires_at=now + timedelta(days=5),
        user_agent=None,
        ip_address=None,
    )
    recently_revoked.revoke(at=now - timedelta(days=1))
    await repo.save(recently_revoked)

    deleted = await repo.purge_older_than(now - timedelta(days=30))

    assert deleted == 0
    assert await repo.get_by_token_hash(hash_refresh_token("still-active")) is not None
    assert (
        await repo.get_by_token_hash(hash_refresh_token("recently-revoked"))
        is not None
    )
