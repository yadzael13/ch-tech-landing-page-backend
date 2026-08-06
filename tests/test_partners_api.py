import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Partner, User


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


async def test_list_partners(db_session: AsyncSession) -> None:
    db_session.add_all(
        [Partner(name="Zeta Cloud"), Partner(name="Amazon Web Services")]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/partners")

    assert response.status_code == 200
    names = [item["name"] for item in response.json()["data"]]
    assert names == ["Amazon Web Services", "Zeta Cloud"]


@pytest.mark.usefixtures("db_session")
async def test_create_partner_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/partners", json={"name": "New Partner"}
        )

    assert response.status_code == 401


async def test_create_partner_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/partners",
            json={"name": "Brand New"},
            headers=_auth(token),
        )

    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Brand New"


async def test_update_partner_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    entity = Partner(name="Old Name")
    db_session.add(entity)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/partners/{entity.id}",
            json={"name": "New Name"},
            headers=_auth(token),
        )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "New Name"


async def test_update_partner_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/partners/{uuid.uuid4()}",
            json={"name": "Whatever"},
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_delete_partner_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    entity = Partner(name="To Delete")
    db_session.add(entity)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/partners/{entity.id}", headers=_auth(token)
        )

    assert response.status_code == 204


async def test_delete_partner_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/partners/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404
