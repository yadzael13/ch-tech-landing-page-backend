import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Client, Project, Testimonial, User


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


async def test_list_testimonials(db_session: AsyncSession) -> None:
    db_session.add(Testimonial(author_name="Ada Lovelace", content="Great work."))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/testimonials")

    assert response.status_code == 200
    names = [item["author_name"] for item in response.json()["data"]]
    assert names == ["Ada Lovelace"]


@pytest.mark.usefixtures("db_session")
async def test_create_testimonial_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/testimonials",
            json={"author_name": "New Author", "content": "Great work."},
        )

    assert response.status_code == 401


async def test_create_testimonial_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/testimonials",
            json={"author_name": "Brand New", "content": "Great work."},
            headers=_auth(token),
        )

    assert response.status_code == 201
    assert response.json()["data"]["author_name"] == "Brand New"


async def test_create_testimonial_with_client_and_project_references(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)
    client_row = Client(name="Acme Corp")
    project_row = Project(slug="sample", title="Sample", visibility="PUBLIC")
    db_session.add_all([client_row, project_row])
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/testimonials",
            json={
                "author_name": "Ada Lovelace",
                "content": "Great work.",
                "client_id": str(client_row.id),
                "project_id": str(project_row.id),
            },
            headers=_auth(token),
        )

    assert response.status_code == 201
    assert response.json()["data"]["client_id"] == str(client_row.id)


async def test_create_testimonial_rejects_a_rating_outside_1_to_5(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/testimonials",
            json={"author_name": "Ada Lovelace", "content": "Great work.", "rating": 6},
            headers=_auth(token),
        )

    assert response.status_code == 422


async def test_create_testimonial_rejects_an_unknown_client(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/testimonials",
            json={
                "author_name": "Ada Lovelace",
                "content": "Great work.",
                "client_id": str(uuid.uuid4()),
            },
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_update_testimonial_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    entity = Testimonial(author_name="Old Name", content="Old content.")
    db_session.add(entity)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/testimonials/{entity.id}",
            json={"author_name": "New Name", "content": "New content."},
            headers=_auth(token),
        )

    assert response.status_code == 200
    assert response.json()["data"]["author_name"] == "New Name"


async def test_update_testimonial_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/testimonials/{uuid.uuid4()}",
            json={"author_name": "Whatever", "content": "Whatever."},
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_delete_testimonial_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    entity = Testimonial(author_name="To Delete", content="Content.")
    db_session.add(entity)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/testimonials/{entity.id}", headers=_auth(token)
        )

    assert response.status_code == 204


async def test_delete_testimonial_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/testimonials/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404
