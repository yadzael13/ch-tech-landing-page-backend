import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import ServiceLine, User


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


async def test_list_service_lines(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            ServiceLine(slug="software-engineering", name="Software Engineering"),
            ServiceLine(slug="ai-automation", name="AI & Automation"),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/service-lines")

    assert response.status_code == 200
    slugs = {item["slug"] for item in response.json()["data"]}
    assert slugs == {"software-engineering", "ai-automation"}


async def test_get_service_line_by_slug(db_session: AsyncSession) -> None:
    db_session.add(ServiceLine(slug="digital-solutions", name="Digital Solutions"))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/service-lines/digital-solutions")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Digital Solutions"


@pytest.mark.usefixtures("db_session")
async def test_get_service_line_404_for_unknown_slug() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/service-lines/does-not-exist")

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_create_service_line_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/service-lines",
            json={"slug": "saas-products", "name": "SaaS Products"},
        )

    assert response.status_code == 401


async def test_create_service_line_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/service-lines",
            json={"slug": "saas-products", "name": "SaaS Products"},
            headers=_auth(token),
        )

    assert response.status_code == 201
    assert response.json()["data"]["slug"] == "saas-products"


async def test_create_service_line_rejects_duplicate_slug(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)
    db_session.add(ServiceLine(slug="taken", name="Taken"))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/service-lines",
            json={"slug": "taken", "name": "Also Taken"},
            headers=_auth(token),
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_update_service_line_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    line = ServiceLine(slug="to-update", name="Old Name")
    db_session.add(line)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/service-lines/{line.id}",
            json={"slug": "to-update", "name": "New Name"},
            headers=_auth(token),
        )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "New Name"


async def test_update_service_line_404_for_unknown_id(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/service-lines/{uuid.uuid4()}",
            json={"slug": "whatever", "name": "Whatever"},
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_delete_service_line_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    line = ServiceLine(slug="to-delete", name="To Delete")
    db_session.add(line)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/service-lines/{line.id}", headers=_auth(token)
        )

    assert response.status_code == 204


async def test_delete_service_line_404_for_unknown_id(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/service-lines/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404
