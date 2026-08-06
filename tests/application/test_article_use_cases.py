import uuid
from datetime import UTC, datetime

import pytest

from app.application.ports.article_repository import (
    ArticleInput,
    ArticleWithTechnologies,
)
from app.application.use_cases.articles import (
    CreateArticle,
    DeleteArticle,
    GetArticleById,
    GetArticleBySlug,
    ListArticles,
    UpdateArticle,
)
from app.core.errors import ConflictError, ResourceNotFoundError
from app.domain.article import Article
from app.domain.value_objects import MarkdownContent, Slug
from tests.application.fakes import InMemoryArticleRepository


def _article(**overrides: object) -> ArticleWithTechnologies:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "author_id": uuid.uuid4(),
        "slug": Slug("sample"),
        "title": "Sample",
        "summary": None,
        "content": MarkdownContent("body"),
        "cover_image": None,
        "reading_time": None,
        "published": False,
        "published_at": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return ArticleWithTechnologies(article=Article(**defaults), technologies=[])  # type: ignore[arg-type]


def _input(**overrides: object) -> ArticleInput:
    defaults: dict[str, object] = {
        "slug": "new-article",
        "title": "New Article",
        "summary": None,
        "content": "body",
        "reading_time": None,
        "published": False,
        "published_at": None,
    }
    defaults.update(overrides)
    return ArticleInput(**defaults)  # type: ignore[arg-type]


async def test_list_articles_hides_drafts_when_published_only() -> None:
    published = _article(published=True, published_at=datetime.now(UTC))
    draft = _article(published=False)
    repo = InMemoryArticleRepository([published, draft])
    use_case = ListArticles(repository=repo)

    result = await use_case.execute(published_only=True, page=1, limit=20)

    assert [r.article.id for r in result] == [published.article.id]


async def test_get_article_by_slug_raises_not_found_when_missing() -> None:
    use_case = GetArticleBySlug(repository=InMemoryArticleRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute("missing", published_only=True)


async def test_get_article_by_id_raises_not_found_when_missing() -> None:
    use_case = GetArticleById(repository=InMemoryArticleRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_create_article_stores_the_given_author_id() -> None:
    repo = InMemoryArticleRepository()
    use_case = CreateArticle(repository=repo)
    author_id = uuid.uuid4()

    result = await use_case.execute(_input(slug="brand-new"), author_id=author_id)

    assert result.article.author_id == author_id


async def test_create_article_rejects_a_duplicate_slug() -> None:
    repo = InMemoryArticleRepository([_article(slug=Slug("taken"))])
    use_case = CreateArticle(repository=repo)

    with pytest.raises(ConflictError):
        await use_case.execute(_input(slug="taken"), author_id=uuid.uuid4())


async def test_update_article_raises_not_found_when_missing() -> None:
    use_case = UpdateArticle(repository=InMemoryArticleRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4(), _input())


async def test_update_article_applies_changes() -> None:
    row = _article(title="Old Title")
    repo = InMemoryArticleRepository([row])
    use_case = UpdateArticle(repository=repo)

    result = await use_case.execute(
        row.article.id, _input(slug=str(row.article.slug), title="New Title")
    )

    assert result.article.title == "New Title"


async def test_delete_article_raises_not_found_when_missing() -> None:
    use_case = DeleteArticle(repository=InMemoryArticleRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_delete_article_removes_it() -> None:
    row = _article()
    repo = InMemoryArticleRepository([row])
    use_case = DeleteArticle(repository=repo)

    await use_case.execute(row.article.id)

    assert await repo.get_by_id(row.article.id) is None
