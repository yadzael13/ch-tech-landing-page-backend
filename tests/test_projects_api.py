import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import get_redis
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Project, Technology, User


async def _create_admin(db_session: AsyncSession) -> tuple[User, str]:
    user = User(
        name="Admin",
        email=f"{uuid.uuid4()}@ch-tech.dev",
        password_hash=hash_password("s3cret-pass"),
    )
    db_session.add(user)
    await db_session.flush()
    token = create_access_token(subject=str(user.id), role=user.role)
    return user, token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_list_projects_only_returns_public_visibility(
    db_session: AsyncSession,
) -> None:
    db_session.add_all(
        [
            Project(slug="public-one", title="Public One", visibility="PUBLIC"),
            Project(slug="private-one", title="Private One", visibility="PRIVATE"),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/projects")

    assert response.status_code == 200
    slugs = {item["slug"] for item in response.json()["data"]}
    assert slugs == {"public-one"}


async def test_list_projects_response_shape_matches_api_md(
    db_session: AsyncSession,
) -> None:
    db_session.add(
        Project(
            slug="shape-check", title="Shape Check", visibility="PUBLIC", featured=True
        )
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/projects")

    item = response.json()["data"][0]
    assert set(item.keys()) == {"id", "slug", "title", "featured"}


async def test_list_projects_filters_by_featured(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            Project(
                slug="featured-one",
                title="Featured",
                visibility="PUBLIC",
                featured=True,
            ),
            Project(
                slug="not-featured",
                title="Not Featured",
                visibility="PUBLIC",
                featured=False,
            ),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/projects", params={"featured": "true"})

    slugs = {item["slug"] for item in response.json()["data"]}
    assert slugs == {"featured-one"}


async def test_list_projects_filters_by_status(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            Project(
                slug="completed-one",
                title="Completed",
                visibility="PUBLIC",
                status="COMPLETED",
            ),
            Project(
                slug="planning-one",
                title="Planning",
                visibility="PUBLIC",
                status="PLANNING",
            ),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/projects", params={"status": "COMPLETED"})

    slugs = {item["slug"] for item in response.json()["data"]}
    assert slugs == {"completed-one"}


async def test_list_projects_filters_by_technology(db_session: AsyncSession) -> None:
    python = Technology(name="Python", category="Language")
    with_tech = Project(slug="with-python", title="With Python", visibility="PUBLIC")
    with_tech.technologies = [python]
    without_tech = Project(
        slug="without-python", title="Without Python", visibility="PUBLIC"
    )
    db_session.add_all([with_tech, without_tech])
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/projects", params={"technology": "Python"})

    slugs = {item["slug"] for item in response.json()["data"]}
    assert slugs == {"with-python"}


async def test_list_projects_search_by_title(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            Project(
                slug="ch-tech-site", title="CH-TECH Portfolio", visibility="PUBLIC"
            ),
            Project(slug="other", title="Something Else", visibility="PUBLIC"),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/projects", params={"search": "portfolio"})

    slugs = {item["slug"] for item in response.json()["data"]}
    assert slugs == {"ch-tech-site"}


async def test_list_projects_pagination(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            Project(slug=f"proj-{i}", title=f"Project {i}", visibility="PUBLIC")
            for i in range(5)
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/projects", params={"page": 1, "limit": 2})

    assert len(response.json()["data"]) == 2


async def test_get_project_by_slug_returns_full_detail(
    db_session: AsyncSession,
) -> None:
    project = Project(
        slug="detail-check",
        title="Detail Check",
        visibility="PUBLIC",
        short_description="short",
    )
    db_session.add(project)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/projects/detail-check")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["slug"] == "detail-check"
    assert body["short_description"] == "short"
    assert body["technologies"] == []


async def test_get_project_by_slug_404_for_private_project(
    db_session: AsyncSession,
) -> None:
    db_session.add(Project(slug="secret-project", title="Secret", visibility="PRIVATE"))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/projects/secret-project")

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_get_project_by_slug_404_for_unknown_slug() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/projects/does-not-exist")

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_admin_list_projects_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/projects")

    assert response.status_code == 401


async def test_admin_list_projects_returns_every_visibility(
    db_session: AsyncSession,
) -> None:
    _, token = await _create_admin(db_session)
    db_session.add_all(
        [
            Project(slug="admin-public", title="Public", visibility="PUBLIC"),
            Project(slug="admin-private", title="Private", visibility="PRIVATE"),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/projects", headers=_auth(token))

    assert response.status_code == 200
    slugs = {item["slug"] for item in response.json()["data"]}
    assert slugs == {"admin-public", "admin-private"}


@pytest.mark.usefixtures("db_session")
async def test_admin_get_project_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/admin/projects/{uuid.uuid4()}")

    assert response.status_code == 401


async def test_admin_get_project_returns_private_project_by_id(
    db_session: AsyncSession,
) -> None:
    _, token = await _create_admin(db_session)
    project = Project(
        slug="admin-detail-check", title="Detail Check", visibility="PRIVATE"
    )
    db_session.add(project)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/admin/projects/{project.id}", headers=_auth(token)
        )

    assert response.status_code == 200
    assert response.json()["data"]["slug"] == "admin-detail-check"


async def test_admin_get_project_404_for_unknown_id(db_session: AsyncSession) -> None:
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/admin/projects/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_create_project_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/projects",
            json={"slug": "new-one", "title": "New One"},
        )

    assert response.status_code == 401


async def test_create_project_succeeds_as_admin(db_session: AsyncSession) -> None:
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/projects",
            json={"slug": "brand-new", "title": "Brand New"},
            headers=_auth(token),
        )

    assert response.status_code == 201
    assert response.json()["data"]["slug"] == "brand-new"


async def test_create_project_rejects_duplicate_slug(
    db_session: AsyncSession,
) -> None:
    _, token = await _create_admin(db_session)
    db_session.add(Project(slug="taken", title="Taken", visibility="PUBLIC"))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/projects",
            json={"slug": "taken", "title": "Also Taken"},
            headers=_auth(token),
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_create_project_requires_title(db_session: AsyncSession) -> None:
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/projects",
            json={"slug": "no-title"},
            headers=_auth(token),
        )

    assert response.status_code == 422


async def test_create_project_rejects_a_malformed_repository_url(
    db_session: AsyncSession,
) -> None:
    # Url/Image value objects (ADR-0012, DATA_MODEL.md) validate this
    # field's shape at the API boundary via ProjectWrite (schemas/project.py)
    # — previously accepted as any free-text string.
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/projects",
            json={
                "slug": "bad-url",
                "title": "Bad URL",
                "repository_url": "not-a-url",
            },
            headers=_auth(token),
        )

    assert response.status_code == 422


async def test_create_project_accepts_a_well_formed_repository_url(
    db_session: AsyncSession,
) -> None:
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/projects",
            json={
                "slug": "good-url",
                "title": "Good URL",
                "repository_url": "https://github.com/ch-tech/ch-tech",
            },
            headers=_auth(token),
        )

    assert response.status_code == 201
    assert (
        response.json()["data"]["repository_url"]
        == "https://github.com/ch-tech/ch-tech"
    )


async def test_update_project_succeeds_as_admin(db_session: AsyncSession) -> None:
    _, token = await _create_admin(db_session)
    project = Project(slug="to-update", title="Old Title", visibility="PUBLIC")
    db_session.add(project)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/projects/{project.id}",
            json={"slug": "to-update", "title": "New Title"},
            headers=_auth(token),
        )

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "New Title"


async def test_update_project_404_for_unknown_id(db_session: AsyncSession) -> None:
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/projects/{uuid.uuid4()}",
            json={"slug": "whatever", "title": "Whatever"},
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_delete_project_succeeds_as_admin(db_session: AsyncSession) -> None:
    _, token = await _create_admin(db_session)
    project = Project(slug="to-delete", title="To Delete", visibility="PUBLIC")
    db_session.add(project)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/projects/{project.id}", headers=_auth(token)
        )

    assert response.status_code == 204


async def test_delete_project_with_technologies_cleans_up_the_relation(
    db_session: AsyncSession,
) -> None:
    _, token = await _create_admin(db_session)
    project = Project(
        slug="to-delete-with-tech", title="To Delete", visibility="PUBLIC"
    )
    project.technologies = [Technology(name="Python", category="Language")]
    db_session.add(project)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/projects/{project.id}", headers=_auth(token)
        )

    assert response.status_code == 204


async def test_delete_project_404_for_unknown_id(db_session: AsyncSession) -> None:
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/projects/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404


async def test_list_projects_is_rate_limited(db_session: AsyncSession) -> None:
    db_session.add(Project(slug="rl-check", title="RL Check", visibility="PUBLIC"))
    await db_session.commit()

    # Every other test in this file also hits GET /projects from the same
    # client IP (127.0.0.1), sharing this exact rate-limit key — start this
    # test's own 100-request budget from zero regardless of what they used.
    await get_redis().delete("ratelimit:public-api:127.0.0.1")

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(100):
                response = await client.get("/api/v1/projects")
                assert response.status_code == 200

            over_limit = await client.get("/api/v1/projects")

        assert over_limit.status_code == 429
    finally:
        await get_redis().delete("ratelimit:public-api:127.0.0.1")
