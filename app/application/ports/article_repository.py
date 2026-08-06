"""ArticleRepository port (ADR-0012, ARCHITECTURE.md, Fase 4)."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from app.domain.article import Article
from app.domain.technology import Technology


@dataclass(slots=True)
class ArticleInput:
    slug: str
    title: str
    summary: str | None
    content: str
    reading_time: int | None
    published: bool
    published_at: datetime | None
    technology_ids: list[uuid.UUID] = field(default_factory=list)
    cover_image: str | None = None


@dataclass(slots=True)
class ArticleWithTechnologies:
    article: Article
    technologies: list[Technology]


class ArticleRepository(Protocol):
    async def list(
        self, *, published_only: bool, page: int, limit: int
    ) -> list[ArticleWithTechnologies]: ...

    async def get_by_slug(
        self, slug: str, *, published_only: bool
    ) -> ArticleWithTechnologies | None: ...

    async def get_by_id(
        self, article_id: uuid.UUID
    ) -> ArticleWithTechnologies | None: ...

    async def create(
        self, data: ArticleInput, *, author_id: uuid.UUID
    ) -> ArticleWithTechnologies: ...

    async def update(
        self, article_id: uuid.UUID, data: ArticleInput
    ) -> ArticleWithTechnologies | None: ...

    async def delete(self, article_id: uuid.UUID) -> bool: ...
