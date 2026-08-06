"""Article entity (DATA_MODEL.md).

Mirrors the invariant already enforced at the database level
(ck_articles_published_requires_published_at, app.models.article): a
published article must have a publish date.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects import Image, MarkdownContent, Slug


@dataclass(slots=True)
class Article:
    id: uuid.UUID
    author_id: uuid.UUID
    slug: Slug
    title: str
    summary: str | None
    content: MarkdownContent
    cover_image: Image | None
    reading_time: int | None
    published: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if self.published and self.published_at is None:
            raise ValueError("A published article requires published_at")
