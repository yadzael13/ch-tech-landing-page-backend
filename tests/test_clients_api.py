import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Client, User


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


async def test_list_clients(db_session: AsyncSession) -> None:
    db_session.add_all([Client(name="Zeta Inc"), Client(name="Acme Corp")])
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/clients")

    assert response.status_code == 200
    names = [item["name"] for item in response.json()["data"]]
    assert names == ["Acme Corp", "Zeta Inc"]


@pytest.mark.usefixtures("db_session")
async def test_create_client_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/clients", json={"name": "New Client"}
        )

    assert response.status_code == 401


async def test_create_client_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/clients",
            json={"name": "Brand New"},
            headers=_auth(token),
        )

    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Brand New"


async def test_create_client_rejects_a_malformed_website_url(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/clients",
            json={"name": "Bad URL", "website_url": "not-a-url"},
            headers=_auth(token),
        )

    assert response.status_code == 422


async def test_update_client_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    entity = Client(name="Old Name")
    db_session.add(entity)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/clients/{entity.id}",
            json={"name": "New Name"},
            headers=_auth(token),
        )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "New Name"


async def test_update_client_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/clients/{uuid.uuid4()}",
            json={"name": "Whatever"},
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_delete_client_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    entity = Client(name="To Delete")
    db_session.add(entity)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/clients/{entity.id}", headers=_auth(token)
        )

    assert response.status_code == 204


async def test_delete_client_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/clients/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404
