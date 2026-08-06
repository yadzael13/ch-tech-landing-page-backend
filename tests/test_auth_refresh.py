from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, hash_refresh_token
from app.main import app
from app.models import RefreshToken, User


async def _create_user(db_session: AsyncSession) -> User:
    user = User(
        name="Yadzael",
        email="yadzael@ch-tech.dev",
        password_hash=hash_password("s3cret-pass"),
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def _issue_refresh_token(
    db_session: AsyncSession,
    user: User,
    *,
    raw_token: str = "raw-refresh-token",
    expires_in: timedelta = timedelta(days=7),
    revoked: bool = False,
) -> RefreshToken:
    now = datetime.now(UTC)
    token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),
        issued_at=now,
        expires_at=now + expires_in,
        revoked_at=now if revoked else None,
    )
    db_session.add(token)
    await db_session.commit()
    return token


async def test_refresh_with_valid_token_returns_new_tokens(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    await _issue_refresh_token(db_session, user, raw_token="valid-token")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "valid-token"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["refresh_token"] != "valid-token"


async def test_refresh_revokes_the_old_token_and_rotates(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    old_token = await _issue_refresh_token(db_session, user, raw_token="old-token")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/auth/refresh", json={"refresh_token": "old-token"})

    await db_session.refresh(old_token)
    assert old_token.revoked_at is not None

    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    assert len(result.scalars().all()) == 2


async def test_refresh_rejects_an_already_used_token(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    await _issue_refresh_token(db_session, user, raw_token="reused-token")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "reused-token"}
        )
        second = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "reused-token"}
        )

    assert first.status_code == 200
    assert second.status_code == 401


async def test_refresh_rejects_an_expired_token(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _issue_refresh_token(
        db_session, user, raw_token="expired-token", expires_in=timedelta(days=-1)
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "expired-token"}
        )

    assert response.status_code == 401


async def test_refresh_rejects_an_already_revoked_token(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    await _issue_refresh_token(
        db_session, user, raw_token="revoked-token", revoked=True
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "revoked-token"}
        )

    assert response.status_code == 401


async def test_refresh_rejects_a_deactivated_user(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await _issue_refresh_token(db_session, user, raw_token="deactivated-user-token")
    user.is_active = False
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "deactivated-user-token"}
        )

    assert response.status_code == 401


@pytest.mark.usefixtures("db_session")
async def test_refresh_rejects_an_unknown_token() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "does-not-exist"}
        )

    assert response.status_code == 401
