import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import get_redis
from app.core.security import hash_password
from app.main import app
from app.models import RefreshToken, User


async def _create_user(db_session: AsyncSession, email: str | None = None) -> User:
    # Unique by default: the login rate limiter keys on email, so tests that
    # share one hardcoded address would silently share — and eventually trip
    # — the same Redis counter across runs (Redis isn't reset like Postgres).
    user = User(
        name="Yadzael",
        email=email or f"{uuid.uuid4()}@ch-tech.dev",
        password_hash=hash_password("s3cret-pass"),
    )
    db_session.add(user)
    await db_session.commit()
    return user


async def test_login_with_valid_credentials_returns_tokens(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "s3cret-pass"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "Bearer"
    assert body["access_token"]
    assert body["refresh_token"]


async def test_login_creates_a_refresh_token_record(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "s3cret-pass"},
        )

    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    tokens = result.scalars().all()

    assert len(tokens) == 1


async def test_login_is_case_insensitive_on_email(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": user.email.upper(), "password": "s3cret-pass"},
        )

    assert response.status_code == 200


async def test_login_rejects_wrong_password(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "wrong"},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_login_rejects_an_oversized_password_with_422_not_500(
    db_session: AsyncSession,
) -> None:
    # A >72-byte password against a real email must fail the same way as
    # against a nonexistent one — a 500 here vs. a 401 there is what makes
    # the endpoint an email-enumeration oracle.
    user = await _create_user(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "a" * 100},
        )

    assert response.status_code == 422


async def test_login_rejects_a_deactivated_user(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    user.is_active = False
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "s3cret-pass"},
        )

    assert response.status_code == 401


@pytest.mark.usefixtures("db_session")
async def test_login_rejects_unknown_email() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": f"{uuid.uuid4()}@ch-tech.dev", "password": "whatever"},
        )

    assert response.status_code == 401


async def test_login_rate_limits_after_five_attempts(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    email = user.email

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(5):
                response = await client.post(
                    "/api/v1/auth/login",
                    json={"email": email, "password": "s3cret-pass"},
                )
                assert response.status_code == 200

            sixth = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "s3cret-pass"},
            )

        assert sixth.status_code == 429
        assert sixth.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    finally:
        await get_redis().delete(f"ratelimit:login:{email}")
