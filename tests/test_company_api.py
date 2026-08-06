import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Company, User


async def _create_admin(db_session: AsyncSession) -> str:
    user = User(
        name="Admin",
        email=f"{uuid.uuid4()}@ch-tech.dev",
        password_hash=hash_password("s3cret-pass"),
    )
    db_session.add(user)
    await db_session.flush()
    return create_access_token(subject=str(user.id), role=user.role)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_get_company_returns_the_singleton(db_session: AsyncSession) -> None:
    db_session.add(Company(legal_name="CH-TECH", display_name="CH-TECH"))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/company")

    assert response.status_code == 200
    assert response.json()["data"]["display_name"] == "CH-TECH"


@pytest.mark.usefixtures("db_session")
async def test_get_company_404_when_never_seeded() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/company")

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_update_company_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            "/api/v1/admin/company",
            json={"legal_name": "CH-TECH", "display_name": "CH-TECH"},
        )

    assert response.status_code == 401


async def test_update_company_creates_it_when_missing(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            "/api/v1/admin/company",
            json={
                "legal_name": "CH-TECH S.A. de C.V.",
                "display_name": "CH-TECH",
                "tagline": "Ingeniería de software e IA.",
            },
            headers=_auth(token),
        )

    assert response.status_code == 200
    assert response.json()["data"]["tagline"] == "Ingeniería de software e IA."


async def test_update_company_replaces_the_existing_singleton(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)
    company = Company(
        legal_name="CH-TECH", display_name="CH-TECH", tagline="Old tagline"
    )
    db_session.add(company)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            "/api/v1/admin/company",
            json={
                "legal_name": "CH-TECH",
                "display_name": "CH-TECH",
                "tagline": "New tagline",
            },
            headers=_auth(token),
        )

    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(company.id)
    assert response.json()["data"]["tagline"] == "New tagline"


async def test_update_company_rejects_a_malformed_email(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            "/api/v1/admin/company",
            json={
                "legal_name": "CH-TECH",
                "display_name": "CH-TECH",
                "email": "not-an-email",
            },
            headers=_auth(token),
        )

    assert response.status_code == 422
