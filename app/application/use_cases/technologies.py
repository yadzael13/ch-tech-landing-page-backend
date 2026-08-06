"""Technology use cases (ADR-0012, Fase 4)."""

import uuid
from dataclasses import dataclass

from app.application.ports.technology_repository import (
    TechnologyFilters,
    TechnologyInput,
    TechnologyRepository,
)
from app.core.errors import ResourceNotFoundError
from app.domain.technology import Technology


@dataclass(slots=True)
class ListTechnologies:
    repository: TechnologyRepository

    async def execute(self, filters: TechnologyFilters) -> list[Technology]:
        return await self.repository.list(filters)


@dataclass(slots=True)
class GetTechnologyById:
    repository: TechnologyRepository

    async def execute(self, technology_id: uuid.UUID) -> Technology:
        result = await self.repository.get_by_id(technology_id)
        if result is None:
            raise ResourceNotFoundError("Technology not found")
        return result


@dataclass(slots=True)
class CreateTechnology:
    repository: TechnologyRepository

    async def execute(self, data: TechnologyInput) -> Technology:
        return await self.repository.create(data)


@dataclass(slots=True)
class UpdateTechnology:
    repository: TechnologyRepository

    async def execute(
        self, technology_id: uuid.UUID, data: TechnologyInput
    ) -> Technology:
        result = await self.repository.update(technology_id, data)
        if result is None:
            raise ResourceNotFoundError("Technology not found")
        return result


@dataclass(slots=True)
class DeleteTechnology:
    repository: TechnologyRepository

    async def execute(self, technology_id: uuid.UUID) -> None:
        deleted = await self.repository.delete(technology_id)
        if not deleted:
            raise ResourceNotFoundError("Technology not found")
