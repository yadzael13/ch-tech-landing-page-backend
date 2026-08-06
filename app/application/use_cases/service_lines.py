"""ServiceLine use cases (ADR-0012, Fase 6)."""

import uuid
from dataclasses import dataclass

from app.application.ports.service_line_repository import (
    ServiceLineInput,
    ServiceLineRepository,
)
from app.core.errors import ResourceNotFoundError
from app.domain.service_line import ServiceLine


@dataclass(slots=True)
class ListServiceLines:
    repository: ServiceLineRepository

    async def execute(self) -> list[ServiceLine]:
        return await self.repository.list()


@dataclass(slots=True)
class GetServiceLineBySlug:
    repository: ServiceLineRepository

    async def execute(self, slug: str) -> ServiceLine:
        result = await self.repository.get_by_slug(slug)
        if result is None:
            raise ResourceNotFoundError("Service line not found")
        return result


@dataclass(slots=True)
class CreateServiceLine:
    repository: ServiceLineRepository

    async def execute(self, data: ServiceLineInput) -> ServiceLine:
        return await self.repository.create(data)


@dataclass(slots=True)
class UpdateServiceLine:
    repository: ServiceLineRepository

    async def execute(
        self, service_line_id: uuid.UUID, data: ServiceLineInput
    ) -> ServiceLine:
        result = await self.repository.update(service_line_id, data)
        if result is None:
            raise ResourceNotFoundError("Service line not found")
        return result


@dataclass(slots=True)
class DeleteServiceLine:
    repository: ServiceLineRepository

    async def execute(self, service_line_id: uuid.UUID) -> None:
        deleted = await self.repository.delete(service_line_id)
        if not deleted:
            raise ResourceNotFoundError("Service line not found")
