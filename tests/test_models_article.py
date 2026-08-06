import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import utcnow
from app.models.article import Article
from app.models.technology import Technology
from app.models.user import User


async def _create_author(db_session: AsyncSession) -> User:
    user = User(name="Yadzael", email="yadzael@ch-tech.dev", password_hash="hashed")
    db_session.add(user)
    await db_session.flush()
    return user


async def test_article_defaults(db_session: AsyncSession) -> None:
    author = await _create_author(db_session)
    article = Article(
        author_id=author.id, slug="hello-world", title="Hello World", content="..."
    )
    db_session.add(article)
    await db_session.commit()

    assert article.published is False
    assert article.published_at is None


async def test_article_slug_must_be_unique(db_session: AsyncSession) -> None:
    author = await _create_author(db_session)
    db_session.add(Article(author_id=author.id, slug="dup", title="A", content="..."))
    await db_session.commit()

    db_session.add(Article(author_id=author.id, slug="dup", title="B", content="..."))
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_published_article_requires_published_at(
    db_session: AsyncSession,
) -> None:
    author = await _create_author(db_session)
    db_session.add(
        Article(
            author_id=author.id,
            slug="no-published-at",
            title="Bad",
            content="...",
            published=True,
            published_at=None,
        )
    )
    # MySQL raises CHECK constraint violations as OperationalError (error
    # 3819), not IntegrityError like Postgres.
    with pytest.raises(OperationalError):
        await db_session.commit()


async def test_published_article_with_published_at_is_allowed(
    db_session: AsyncSession,
) -> None:
    author = await _create_author(db_session)
    db_session.add(
        Article(
            author_id=author.id,
            slug="published",
            title="Good",
            content="...",
            published=True,
            published_at=utcnow(),
        )
    )
    await db_session.commit()


async def test_article_technology_many_to_many_relationship(
    db_session: AsyncSession,
) -> None:
    author = await _create_author(db_session)
    article = Article(
        author_id=author.id, slug="stack", title="Our Stack", content="..."
    )
    article.technologies = [Technology(name="Python", category="Language")]

    db_session.add(article)
    await db_session.commit()
    await db_session.refresh(article, attribute_names=["technologies"])

    assert {t.name for t in article.technologies} == {"Python"}
