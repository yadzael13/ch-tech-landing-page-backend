import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.article_repository import ArticleInput
from app.core.errors import ConflictError
from app.infrastructure.repositories.article_repository import (
    SQLAlchemyArticleRepository,
)
from app.models import Technology as TechnologyModel
from app.models import User as UserModel


async def _make_author(db_session: AsyncSession) -> uuid.UUID:
    user = UserModel(
        name="Admin", email=f"{uuid.uuid4()}@ch-tech.dev", password_hash="hash"
    )
    db_session.add(user)
    await db_session.flush()
    return user.id


def _input(**overrides: object) -> ArticleInput:
    defaults: dict[str, object] = {
        "slug": "repo-test",
        "title": "Repo Test",
        "summary": None,
        "content": "body",
        "reading_time": None,
        "published": False,
        "published_at": None,
    }
    defaults.update(overrides)
    return ArticleInput(**defaults)  # type: ignore[arg-type]


async def test_create_persists_and_returns_the_article(
    db_session: AsyncSession,
) -> None:
    author_id = await _make_author(db_session)
    repo = SQLAlchemyArticleRepository(db_session)

    result = await repo.create(_input(slug="brand-new"), author_id=author_id)

    assert str(result.article.slug) == "brand-new"
    assert result.article.author_id == author_id


async def test_create_rejects_a_duplicate_slug(db_session: AsyncSession) -> None:
    author_id = await _make_author(db_session)
    repo = SQLAlchemyArticleRepository(db_session)
    await repo.create(_input(slug="taken"), author_id=author_id)

    with pytest.raises(ConflictError):
        await repo.create(_input(slug="taken"), author_id=author_id)


async def test_create_attaches_the_requested_technologies(
    db_session: AsyncSession,
) -> None:
    author_id = await _make_author(db_session)
    tech = TechnologyModel(name="Python", category="Language")
    db_session.add(tech)
    await db_session.flush()

    repo = SQLAlchemyArticleRepository(db_session)
    result = await repo.create(
        _input(slug="with-tech", technology_ids=[tech.id]), author_id=author_id
    )

    assert [t.name for t in result.technologies] == ["Python"]


async def test_list_hides_drafts_when_published_only(db_session: AsyncSession) -> None:
    author_id = await _make_author(db_session)
    repo = SQLAlchemyArticleRepository(db_session)
    await repo.create(
        _input(slug="published", published=True, published_at=datetime.now(UTC)),
        author_id=author_id,
    )
    await repo.create(_input(slug="draft", published=False), author_id=author_id)

    result = await repo.list(published_only=True, page=1, limit=20)

    assert [str(r.article.slug) for r in result] == ["published"]


async def test_get_by_slug_hides_drafts_when_published_only(
    db_session: AsyncSession,
) -> None:
    author_id = await _make_author(db_session)
    repo = SQLAlchemyArticleRepository(db_session)
    await repo.create(_input(slug="draft"), author_id=author_id)

    assert await repo.get_by_slug("draft", published_only=True) is None
    found = await repo.get_by_slug("draft", published_only=False)
    assert found is not None


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyArticleRepository(db_session)
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_update_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyArticleRepository(db_session)
    assert await repo.update(uuid.uuid4(), _input()) is None


async def test_update_applies_changes(db_session: AsyncSession) -> None:
    author_id = await _make_author(db_session)
    repo = SQLAlchemyArticleRepository(db_session)
    created = await repo.create(
        _input(slug="to-update", title="Old Title"), author_id=author_id
    )

    updated = await repo.update(
        created.article.id, _input(slug="to-update", title="New Title")
    )

    assert updated is not None
    assert updated.article.title == "New Title"


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyArticleRepository(db_session)
    assert await repo.delete(uuid.uuid4()) is False


async def test_delete_removes_the_article(db_session: AsyncSession) -> None:
    author_id = await _make_author(db_session)
    repo = SQLAlchemyArticleRepository(db_session)
    created = await repo.create(_input(slug="to-delete"), author_id=author_id)

    assert await repo.delete(created.article.id) is True
    assert await repo.get_by_id(created.article.id) is None


async def test_delete_with_technologies_cleans_up_the_relation(
    db_session: AsyncSession,
) -> None:
    author_id = await _make_author(db_session)
    tech = TechnologyModel(name="Docker", category="Infra")
    db_session.add(tech)
    await db_session.flush()

    repo = SQLAlchemyArticleRepository(db_session)
    created = await repo.create(
        _input(slug="to-delete-with-tech", technology_ids=[tech.id]),
        author_id=author_id,
    )

    assert await repo.delete(created.article.id) is True
