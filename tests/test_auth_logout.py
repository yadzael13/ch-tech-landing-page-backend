from datetime import UTC, datetime, timedelta

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, hash_refresh_token
from app.main import app
from app.models import RefreshToken, User


async def _create_user(
    db_session: AsyncSession, email: str = "yadzael@ch-tech.dev"
) -> User:
    user = User(name="Yadzael", email=email, password_hash=hash_password("s3cret-pass"))
    db_session.add(user)
    await db_session.flush()
    return user


async def _issue_refresh_token(
    db_session: AsyncSession, user: User, raw_token: str
) -> RefreshToken:
    now = datetime.now(UTC)
    token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),
        issued_at=now,
        expires_at=now + timedelta(days=7),
    )
    db_session.add(token)
    await db_session.commit()
    return token


async def test_logout_without_access_token_returns_401(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    await _issue_refresh_token(db_session, user, "some-token")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/logout", json={"refresh_token": "some-token"}
        )

    assert response.status_code == 401


async def test_logout_with_invalid_access_token_returns_401(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    await _issue_refresh_token(db_session, user, "some-token")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "some-token"},
            headers={"Authorization": "Bearer not-a-real-token"},
        )

    assert response.status_code == 401


async def test_logout_revokes_the_refresh_token(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    token = await _issue_refresh_token(db_session, user, "my-refresh-token")
    access_token = create_access_token(subject=str(user.id), role=user.role)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "my-refresh-token"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert response.status_code == 204
    await db_session.refresh(token)
    assert token.revoked_at is not None


async def test_logout_rejects_a_refresh_token_owned_by_another_user(
    db_session: AsyncSession,
) -> None:
    owner = await _create_user(db_session, email="owner@ch-tech.dev")
    attacker = await _create_user(db_session, email="attacker@ch-tech.dev")
    await _issue_refresh_token(db_session, owner, "owners-token")
    attacker_access_token = create_access_token(
        subject=str(attacker.id), role=attacker.role
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "owners-token"},
            headers={"Authorization": f"Bearer {attacker_access_token}"},
        )

    assert response.status_code == 401


async def test_logout_rejects_an_unknown_refresh_token(
    db_session: AsyncSession,
) -> None:
    user = await _create_user(db_session)
    access_token = create_access_token(subject=str(user.id), role=user.role)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "does-not-exist"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert response.status_code == 401
