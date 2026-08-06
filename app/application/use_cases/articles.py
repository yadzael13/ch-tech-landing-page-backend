"""Article use cases (ADR-0012, Fase 4)."""

import uuid
from dataclasses import dataclass

from app.application.ports.article_repository import (
    ArticleInput,
    ArticleRepository,
    ArticleWithTechnologies,
)
from app.core.errors import ResourceNotFoundError


@dataclass(slots=True)
class ListArticles:
    repository: ArticleRepository

    async def execute(
        self, *, published_only: bool, page: int, limit: int
    ) -> list[ArticleWithTechnologies]:
        return await self.repository.list(
            published_only=published_only, page=page, limit=limit
        )


@dataclass(slots=True)
class GetArticleBySlug:
    repository: ArticleRepository

    async def execute(
        self, slug: str, *, published_only: bool
    ) -> ArticleWithTechnologies:
        result = await self.repository.get_by_slug(slug, published_only=published_only)
        if result is None:
            raise ResourceNotFoundError("Article not found")
        return result


@dataclass(slots=True)
class GetArticleById:
    repository: ArticleRepository

    async def execute(self, article_id: uuid.UUID) -> ArticleWithTechnologies:
        result = await self.repository.get_by_id(article_id)
        if result is None:
            raise ResourceNotFoundError("Article not found")
        return result


@dataclass(slots=True)
class CreateArticle:
    repository: ArticleRepository

    async def execute(
        self, data: ArticleInput, *, author_id: uuid.UUID
    ) -> ArticleWithTechnologies:
        return await self.repository.create(data, author_id=author_id)


@dataclass(slots=True)
class UpdateArticle:
    repository: ArticleRepository

    async def execute(
        self, article_id: uuid.UUID, data: ArticleInput
    ) -> ArticleWithTechnologies:
        result = await self.repository.update(article_id, data)
        if result is None:
            raise ResourceNotFoundError("Article not found")
        return result


@dataclass(slots=True)
class DeleteArticle:
    repository: ArticleRepository

    async def execute(self, article_id: uuid.UUID) -> None:
        deleted = await self.repository.delete(article_id)
        if not deleted:
            raise ResourceNotFoundError("Article not found")
