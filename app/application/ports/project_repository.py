"""ProjectRepository port (ADR-0012, ARCHITECTURE.md).

The application layer depends on this Protocol, never on a concrete
implementation — infrastructure/repositories/project_repository.py provides
the SQLAlchemy adapter; tests/application/fakes.py provides an in-memory one.
"""

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from app.domain.enums import ProjectStatus, Visibility
from app.domain.project import Project
from app.domain.technology import Technology


@dataclass(slots=True)
class ProjectFilters:
    """GET /projects and GET /admin/projects query params (API.md)."""

    technology: str | None = None
    featured: bool | None = None
    status: str | None = None
    search: str | None = None
    sort: str = "created_at"
    page: int = 1
    limit: int = 20


@dataclass(slots=True)
class ProjectInput:
    """Fields accepted by POST/PUT /admin/projects (API.md ProjectWrite).

    repository_url/live_demo_url/cover_image stay plain strings here, not
    Url/Image value objects: ProjectWrite does not validate their format
    today, and this pilot migration must not change that contract.
    """

    slug: str
    title: str
    short_description: str | None
    full_description: str | None
    status: ProjectStatus
    visibility: Visibility
    featured: bool
    started_at: date | None
    finished_at: date | None
    technology_ids: list[uuid.UUID] = field(default_factory=list)
    repository_url: str | None = None
    live_demo_url: str | None = None
    cover_image: str | None = None


@dataclass(slots=True)
class ProjectWithTechnologies:
    project: Project
    technologies: list[Technology]


class ProjectRepository(Protocol):
    async def list(
        self, filters: ProjectFilters, *, public_only: bool
    ) -> list[ProjectWithTechnologies]: ...

    async def get_by_slug(
        self, slug: str, *, public_only: bool
    ) -> ProjectWithTechnologies | None: ...

    async def get_by_id(
        self, project_id: uuid.UUID
    ) -> ProjectWithTechnologies | None: ...

    async def create(self, data: ProjectInput) -> ProjectWithTechnologies: ...

    async def update(
        self, project_id: uuid.UUID, data: ProjectInput
    ) -> ProjectWithTechnologies | None: ...

    async def delete(self, project_id: uuid.UUID) -> bool: ...
