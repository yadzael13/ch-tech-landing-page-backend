import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Service, User


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


async def test_list_services_only_returns_active(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            Service(slug="active-one", title="Active One", active=True),
            Service(slug="inactive-one", title="Inactive One", active=False),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/services")

    assert response.status_code == 200
    slugs = {item["slug"] for item in response.json()["data"]}
    assert slugs == {"active-one"}


async def test_get_service_by_slug(db_session: AsyncSession) -> None:
    db_session.add(Service(slug="consulting", title="Consulting", active=True))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/services/consulting")

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Consulting"


async def test_get_service_404_for_inactive_slug(db_session: AsyncSession) -> None:
    db_session.add(Service(slug="hidden", title="Hidden", active=False))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/services/hidden")

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_get_service_404_for_unknown_slug() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/services/does-not-exist")

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_admin_list_services_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/services")

    assert response.status_code == 401


async def test_admin_list_services_returns_inactive_too(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)
    db_session.add_all(
        [
            Service(slug="admin-active", title="Active", active=True),
            Service(slug="admin-inactive", title="Inactive", active=False),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/services", headers=_auth(token))

    assert response.status_code == 200
    slugs = {item["slug"] for item in response.json()["data"]}
    assert slugs == {"admin-active", "admin-inactive"}


@pytest.mark.usefixtures("db_session")
async def test_admin_get_service_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/admin/services/{uuid.uuid4()}")

    assert response.status_code == 401


async def test_admin_get_service_returns_inactive_service_by_id(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)
    service = Service(slug="admin-detail", title="Detail Check", active=False)
    db_session.add(service)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/admin/services/{service.id}", headers=_auth(token)
        )

    assert response.status_code == 200
    assert response.json()["data"]["slug"] == "admin-detail"


async def test_admin_get_service_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/admin/services/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_create_service_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/services", json={"slug": "new-one", "title": "New One"}
        )

    assert response.status_code == 401


async def test_create_service_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/services",
            json={"slug": "brand-new", "title": "Brand New"},
            headers=_auth(token),
        )

    assert response.status_code == 201
    assert response.json()["data"]["slug"] == "brand-new"


async def test_create_service_rejects_duplicate_slug(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    db_session.add(Service(slug="taken", title="Taken"))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/services",
            json={"slug": "taken", "title": "Also Taken"},
            headers=_auth(token),
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_create_service_requires_title(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/services", json={"slug": "no-title"}, headers=_auth(token)
        )

    assert response.status_code == 422


async def test_update_service_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    service = Service(slug="to-update", title="Old Title")
    db_session.add(service)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/services/{service.id}",
            json={"slug": "to-update", "title": "New Title"},
            headers=_auth(token),
        )

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "New Title"


async def test_update_service_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/services/{uuid.uuid4()}",
            json={"slug": "whatever", "title": "Whatever"},
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_delete_service_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    service = Service(slug="to-delete", title="To Delete")
    db_session.add(service)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/services/{service.id}", headers=_auth(token)
        )

    assert response.status_code == 204


async def test_delete_service_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/services/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404
