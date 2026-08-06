import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Product, User


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


async def test_list_products(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            Product(slug="zeta", name="Zeta", status="WAITLIST"),
            Product(slug="alpha", name="Alpha", status="LIVE"),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/products")

    assert response.status_code == 200
    names = [item["name"] for item in response.json()["data"]]
    assert names == ["Alpha", "Zeta"]


async def test_get_product_by_slug(db_session: AsyncSession) -> None:
    db_session.add(Product(slug="observability", name="Observability", status="BETA"))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/products/observability")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "BETA"


@pytest.mark.usefixtures("db_session")
async def test_get_product_404_for_unknown_slug() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/products/does-not-exist")

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_create_product_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/products", json={"slug": "new-one", "name": "New One"}
        )

    assert response.status_code == 401


async def test_create_product_defaults_to_waitlist(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/products",
            json={"slug": "brand-new", "name": "Brand New"},
            headers=_auth(token),
        )

    assert response.status_code == 201
    assert response.json()["data"]["status"] == "WAITLIST"


async def test_create_product_rejects_duplicate_slug(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    db_session.add(Product(slug="taken", name="Taken", status="WAITLIST"))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/products",
            json={"slug": "taken", "name": "Also Taken"},
            headers=_auth(token),
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_create_product_rejects_an_invalid_status(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/products",
            json={"slug": "bad-status", "name": "Bad", "status": "NOT_A_STATUS"},
            headers=_auth(token),
        )

    assert response.status_code == 422


async def test_update_product_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    entity = Product(slug="to-update", name="Old Name", status="WAITLIST")
    db_session.add(entity)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/products/{entity.id}",
            json={"slug": "to-update", "name": "New Name", "status": "LIVE"},
            headers=_auth(token),
        )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "LIVE"


async def test_update_product_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/products/{uuid.uuid4()}",
            json={"slug": "whatever", "name": "Whatever"},
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_delete_product_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    entity = Product(slug="to-delete", name="To Delete", status="WAITLIST")
    db_session.add(entity)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/products/{entity.id}", headers=_auth(token)
        )

    assert response.status_code == 204


async def test_delete_product_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/products/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404
