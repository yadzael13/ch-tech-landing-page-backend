import uuid
from datetime import UTC, datetime

import pytest

from app.domain.article import Article
from app.domain.value_objects import MarkdownContent, Slug


def _article(**overrides: object) -> Article:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "author_id": uuid.uuid4(),
        "slug": Slug("ch-tech-v2"),
        "title": "CH-TECH V2",
        "summary": None,
        "content": MarkdownContent("# CH-TECH V2"),
        "cover_image": None,
        "reading_time": None,
        "published": False,
        "published_at": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Article(**defaults)  # type: ignore[arg-type]


def test_a_draft_article_needs_no_published_at() -> None:
    article = _article(published=False, published_at=None)
    assert article.published_at is None


def test_a_published_article_requires_published_at() -> None:
    with pytest.raises(ValueError, match="published_at"):
        _article(published=True, published_at=None)


def test_a_published_article_with_a_date_is_valid() -> None:
    published_at = datetime(2026, 1, 2, tzinfo=UTC)
    article = _article(published=True, published_at=published_at)
    assert article.published_at == published_at
