import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.value_objects import Image, MarkdownContent
from app.schemas.project import TechnologySummary


class ArticleListItem(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str | None
    cover_image: str | None
    reading_time: int | None
    published_at: datetime | None

    model_config = {"from_attributes": True}


class ArticleDetail(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str | None
    content: str
    cover_image: str | None
    reading_time: int | None
    published: bool
    published_at: datetime | None
    author_id: uuid.UUID
    technologies: list[TechnologySummary]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArticleWrite(BaseModel):
    """Shared by create (POST) and full replace (PUT). Field lengths mirror
    DATABASE_SCHEMA.md (title VARCHAR(255), slug VARCHAR(150)). The model's
    own CHECK constraint requires published_at whenever published=True — that
    rule is enforced here too, so an invalid combination fails fast with a
    422 instead of surfacing as an opaque DB IntegrityError."""

    slug: str = Field(max_length=150)
    title: str = Field(max_length=255)
    summary: str | None = Field(default=None, max_length=500)
    content: str = Field(max_length=50_000)
    cover_image: str | None = None
    reading_time: int | None = None
    published: bool = False
    published_at: datetime | None = None
    technology_ids: list[uuid.UUID] = []

    @field_validator("content")
    @classmethod
    def _validate_content_shape(cls, value: str) -> str:
        # Reuses the domain MarkdownContent value object (ADR-0012) — a
        # ValueError here becomes a standard 422 VALIDATION_ERROR (API.md).
        MarkdownContent(value)
        return value

    @field_validator("cover_image")
    @classmethod
    def _validate_cover_image_shape(cls, value: str | None) -> str | None:
        if value is not None:
            Image(value)
        return value

    @model_validator(mode="after")
    def _published_requires_published_at(self) -> "ArticleWrite":
        if self.published and self.published_at is None:
            raise ValueError("published_at is required when published is true")
        return self
