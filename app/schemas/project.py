import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.domain.value_objects import Image, Slug, Url
from app.models import ProjectStatus, Visibility


class TechnologySummary(BaseModel):
    id: uuid.UUID
    name: str
    category: str | None

    model_config = {"from_attributes": True}


class ProjectListItem(BaseModel):
    """The exact shape API.md documents for GET /projects."""

    id: uuid.UUID
    slug: str
    title: str
    featured: bool

    model_config = {"from_attributes": True}


class ProjectDetail(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    short_description: str | None
    full_description: str | None
    repository_url: str | None
    live_demo_url: str | None
    cover_image: str | None
    status: str
    visibility: str
    featured: bool
    started_at: date | None
    finished_at: date | None
    technologies: list[TechnologySummary]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectWrite(BaseModel):
    """Shared by create (POST) and full replace (PUT) — API.md validation
    rules: title required (<=255 chars), slug unique, description required."""

    slug: str = Field(max_length=150)
    title: str = Field(max_length=255)
    short_description: str | None = Field(default=None, max_length=500)
    full_description: str | None = Field(default=None, max_length=20_000)
    repository_url: str | None = None
    live_demo_url: str | None = None
    cover_image: str | None = None
    status: ProjectStatus = ProjectStatus.PLANNING
    visibility: Visibility = Visibility.PRIVATE
    featured: bool = False
    started_at: date | None = None
    finished_at: date | None = None
    technology_ids: list[uuid.UUID] = []

    @field_validator("slug")
    @classmethod
    def _validate_slug_shape(cls, value: str) -> str:
        # Reuses the domain Slug value object (ADR-0012, DATA_MODEL.md) so an
        # invalid slug (empty, uppercase, spaces...) is rejected here — a
        # standard 422 — instead of reaching the repository, which used to
        # persist the row and only raise once the response tried to rebuild
        # the domain entity, after the write had already committed.
        Slug(value)
        return value

    @field_validator("repository_url", "live_demo_url")
    @classmethod
    def _validate_url_shape(cls, value: str | None) -> str | None:
        # Reuses the domain Url value object (ADR-0012, DATA_MODEL.md) so the
        # http(s)-URL rule lives in one place. A ValueError here becomes a
        # standard 422 VALIDATION_ERROR (API.md), same as any other field.
        if value is not None:
            Url(value)
        return value

    @field_validator("cover_image")
    @classmethod
    def _validate_cover_image_shape(cls, value: str | None) -> str | None:
        if value is not None:
            Image(value)
        return value
