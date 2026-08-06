"""Project use cases (ADR-0012 — Fase 3 pilot, ARCHITECTURE.md).

Each use case depends only on the ProjectRepository port, never on a
concrete repository — see tests/application/test_project_use_cases.py for
how that's exercised without FastAPI or a real database.
"""

import uuid
from dataclasses import dataclass

from app.application.ports.project_repository import (
    ProjectFilters,
    ProjectInput,
    ProjectRepository,
    ProjectWithTechnologies,
)
from app.core.errors import ResourceNotFoundError


@dataclass(slots=True)
class ListProjects:
    repository: ProjectRepository

    async def execute(
        self, filters: ProjectFilters, *, public_only: bool
    ) -> list[ProjectWithTechnologies]:
        return await self.repository.list(filters, public_only=public_only)


@dataclass(slots=True)
class GetProjectBySlug:
    repository: ProjectRepository

    async def execute(self, slug: str, *, public_only: bool) -> ProjectWithTechnologies:
        result = await self.repository.get_by_slug(slug, public_only=public_only)
        if result is None:
            raise ResourceNotFoundError("Project not found")
        return result


@dataclass(slots=True)
class GetProjectById:
    repository: ProjectRepository

    async def execute(self, project_id: uuid.UUID) -> ProjectWithTechnologies:
        result = await self.repository.get_by_id(project_id)
        if result is None:
            raise ResourceNotFoundError("Project not found")
        return result


@dataclass(slots=True)
class CreateProject:
    repository: ProjectRepository

    async def execute(self, data: ProjectInput) -> ProjectWithTechnologies:
        return await self.repository.create(data)


@dataclass(slots=True)
class UpdateProject:
    repository: ProjectRepository

    async def execute(
        self, project_id: uuid.UUID, data: ProjectInput
    ) -> ProjectWithTechnologies:
        result = await self.repository.update(project_id, data)
        if result is None:
            raise ResourceNotFoundError("Project not found")
        return result


@dataclass(slots=True)
class DeleteProject:
    repository: ProjectRepository

    async def execute(self, project_id: uuid.UUID) -> None:
        deleted = await self.repository.delete(project_id)
        if not deleted:
            raise ResourceNotFoundError("Project not found")
