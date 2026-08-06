import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Article, Technology, User


async def _create_admin(db_session: AsyncSession) -> tuple[User, str]:
    user = User(
        name="Admin",
        email=f"{uuid.uuid4()}@ch-tech.dev",
        password_hash=hash_password("s3cret-pass"),
    )
    db_session.add(user)
    # commit (not flush): article.author_id is a real FK the DB checks from
    # the request's own separate session/connection, so the user row must be
    # durably visible there, not just pending in this session's transaction.
    await db_session.commit()
    token = create_access_token(subject=str(user.id), role=user.role)
    return user, token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_list_articles_only_returns_published(db_session: AsyncSession) -> None:
    author, _ = await _create_admin(db_session)
    db_session.add_all(
        [
            Article(
                slug="published-one",
                title="Published One",
                content="content",
                author_id=author.id,
                published=True,
                published_at=datetime.now(UTC),
            ),
            Article(
                slug="draft-one",
                title="Draft One",
                content="content",
                author_id=author.id,
                published=False,
            ),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/articles")

    assert response.status_code == 200
    slugs = {item["slug"] for item in response.json()["data"]}
    assert slugs == {"published-one"}


async def test_get_article_by_slug_returns_full_detail(
    db_session: AsyncSession,
) -> None:
    author, _ = await _create_admin(db_session)
    article = Article(
        slug="deep-dive",
        title="Deep Dive",
        content="full body content",
        author_id=author.id,
        published=True,
        published_at=datetime.now(UTC),
    )
    db_session.add(article)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/articles/deep-dive")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["content"] == "full body content"
    assert body["technologies"] == []


async def test_get_article_404_for_unpublished_slug(db_session: AsyncSession) -> None:
    author, _ = await _create_admin(db_session)
    db_session.add(
        Article(
            slug="hidden",
            title="Hidden",
            content="content",
            author_id=author.id,
            published=False,
        )
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/articles/hidden")

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_admin_list_articles_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/articles")

    assert response.status_code == 401


async def test_admin_list_articles_returns_unpublished_too(
    db_session: AsyncSession,
) -> None:
    author, token = await _create_admin(db_session)
    db_session.add_all(
        [
            Article(
                slug="admin-published",
                title="Published",
                content="content",
                author_id=author.id,
                published=True,
                published_at=datetime.now(UTC),
            ),
            Article(
                slug="admin-draft",
                title="Draft",
                content="content",
                author_id=author.id,
                published=False,
            ),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/articles", headers=_auth(token))

    assert response.status_code == 200
    slugs = {item["slug"] for item in response.json()["data"]}
    assert slugs == {"admin-published", "admin-draft"}


@pytest.mark.usefixtures("db_session")
async def test_admin_get_article_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/admin/articles/{uuid.uuid4()}")

    assert response.status_code == 401


async def test_admin_get_article_returns_unpublished_by_id(
    db_session: AsyncSession,
) -> None:
    author, token = await _create_admin(db_session)
    article = Article(
        slug="admin-detail",
        title="Detail Check",
        content="content",
        author_id=author.id,
        published=False,
    )
    db_session.add(article)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/admin/articles/{article.id}", headers=_auth(token)
        )

    assert response.status_code == 200
    assert response.json()["data"]["slug"] == "admin-detail"


async def test_admin_get_article_404_for_unknown_id(db_session: AsyncSession) -> None:
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/admin/articles/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_create_article_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/articles",
            json={"slug": "new-one", "title": "New One", "content": "content"},
        )

    assert response.status_code == 401


async def test_create_article_succeeds_as_admin(db_session: AsyncSession) -> None:
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/articles",
            json={"slug": "brand-new", "title": "Brand New", "content": "content"},
            headers=_auth(token),
        )

    assert response.status_code == 201
    assert response.json()["data"]["slug"] == "brand-new"


async def test_create_article_rejects_published_without_published_at(
    db_session: AsyncSession,
) -> None:
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/articles",
            json={
                "slug": "bad-publish",
                "title": "Bad Publish",
                "content": "content",
                "published": True,
            },
            headers=_auth(token),
        )

    assert response.status_code == 422


async def test_create_article_rejects_duplicate_slug(db_session: AsyncSession) -> None:
    author, token = await _create_admin(db_session)
    db_session.add(
        Article(slug="taken", title="Taken", content="content", author_id=author.id)
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/articles",
            json={"slug": "taken", "title": "Also Taken", "content": "content"},
            headers=_auth(token),
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


async def test_create_article_requires_content(db_session: AsyncSession) -> None:
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/articles",
            json={"slug": "no-content", "title": "No Content"},
            headers=_auth(token),
        )

    assert response.status_code == 422


async def test_create_article_rejects_blank_content(db_session: AsyncSession) -> None:
    # MarkdownContent value object (ADR-0012) rejects blank body text.
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/articles",
            json={"slug": "blank-content", "title": "Blank", "content": "   "},
            headers=_auth(token),
        )

    assert response.status_code == 422


async def test_create_article_rejects_a_malformed_cover_image(
    db_session: AsyncSession,
) -> None:
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/articles",
            json={
                "slug": "bad-cover",
                "title": "Bad Cover",
                "content": "content",
                "cover_image": "not-a-url",
            },
            headers=_auth(token),
        )

    assert response.status_code == 422


async def test_update_article_succeeds_as_admin(db_session: AsyncSession) -> None:
    author, token = await _create_admin(db_session)
    article = Article(
        slug="to-update", title="Old Title", content="content", author_id=author.id
    )
    db_session.add(article)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/articles/{article.id}",
            json={"slug": "to-update", "title": "New Title", "content": "content"},
            headers=_auth(token),
        )

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "New Title"


async def test_update_article_404_for_unknown_id(db_session: AsyncSession) -> None:
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/articles/{uuid.uuid4()}",
            json={"slug": "whatever", "title": "Whatever", "content": "content"},
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_delete_article_with_technologies_cleans_up_the_relation(
    db_session: AsyncSession,
) -> None:
    author, token = await _create_admin(db_session)
    article = Article(
        slug="to-delete-with-tech",
        title="To Delete",
        content="content",
        author_id=author.id,
    )
    article.technologies = [Technology(name="Python", category="Language")]
    db_session.add(article)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/articles/{article.id}", headers=_auth(token)
        )

    assert response.status_code == 204


async def test_delete_article_404_for_unknown_id(db_session: AsyncSession) -> None:
    _, token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/articles/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404
