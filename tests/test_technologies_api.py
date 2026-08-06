import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Technology, User


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


async def test_list_technologies(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            Technology(name="Python", category="Language"),
            Technology(name="Docker", category="Infra"),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/technologies")

    assert response.status_code == 200
    names = {item["name"] for item in response.json()["data"]}
    assert names == {"Python", "Docker"}


async def test_list_technologies_filters_by_category(
    db_session: AsyncSession,
) -> None:
    db_session.add_all(
        [
            Technology(name="Python", category="Language"),
            Technology(name="Docker", category="Infra"),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/technologies", params={"category": "Infra"}
        )

    names = {item["name"] for item in response.json()["data"]}
    assert names == {"Docker"}


async def test_get_technology_by_id(db_session: AsyncSession) -> None:
    tech = Technology(name="Python", category="Language")
    db_session.add(tech)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/technologies/{tech.id}")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Python"


@pytest.mark.usefixtures("db_session")
async def test_get_technology_404_for_unknown_id() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/technologies/{uuid.uuid4()}")

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_create_technology_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/technologies", json={"name": "Python"}
        )

    assert response.status_code == 401


async def test_create_technology_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/technologies",
            json={"name": "Rust", "category": "Language"},
            headers=_auth(token),
        )

    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Rust"


async def test_create_technology_requires_name(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/technologies", json={}, headers=_auth(token)
        )

    assert response.status_code == 422


async def test_create_technology_rejects_a_malformed_official_url(
    db_session: AsyncSession,
) -> None:
    # Same rule as Project.repository_url (ADR-0012): TechnologyWrite
    # validates icon/official_url through the domain Url/Image value
    # objects, previously accepted as any free-text string.
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/technologies",
            json={"name": "Bad", "official_url": "not-a-url"},
            headers=_auth(token),
        )

    assert response.status_code == 422


async def test_update_technology_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    tech = Technology(name="Old Name", category="Language")
    db_session.add(tech)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/technologies/{tech.id}",
            json={"name": "New Name", "category": "Language"},
            headers=_auth(token),
        )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "New Name"


async def test_update_technology_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/technologies/{uuid.uuid4()}",
            json={"name": "Whatever"},
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_delete_technology_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    tech = Technology(name="To Delete", category="Language")
    db_session.add(tech)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/technologies/{tech.id}", headers=_auth(token)
        )

    assert response.status_code == 204


async def test_delete_technology_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/technologies/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404
