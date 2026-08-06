"""Service use cases (ADR-0012, Fase 4)."""

import uuid
from dataclasses import dataclass

from app.application.ports.service_repository import ServiceInput, ServiceRepository
from app.core.errors import ResourceNotFoundError
from app.domain.service import Service


@dataclass(slots=True)
class ListServices:
    repository: ServiceRepository

    async def execute(self, *, active_only: bool) -> list[Service]:
        return await self.repository.list(active_only=active_only)


@dataclass(slots=True)
class GetServiceBySlug:
    repository: ServiceRepository

    async def execute(self, slug: str, *, active_only: bool) -> Service:
        result = await self.repository.get_by_slug(slug, active_only=active_only)
        if result is None:
            raise ResourceNotFoundError("Service not found")
        return result


@dataclass(slots=True)
class GetServiceById:
    repository: ServiceRepository

    async def execute(self, service_id: uuid.UUID) -> Service:
        result = await self.repository.get_by_id(service_id)
        if result is None:
            raise ResourceNotFoundError("Service not found")
        return result


@dataclass(slots=True)
class CreateService:
    repository: ServiceRepository

    async def execute(self, data: ServiceInput) -> Service:
        return await self.repository.create(data)


@dataclass(slots=True)
class UpdateService:
    repository: ServiceRepository

    async def execute(self, service_id: uuid.UUID, data: ServiceInput) -> Service:
        result = await self.repository.update(service_id, data)
        if result is None:
            raise ResourceNotFoundError("Service not found")
        return result


@dataclass(slots=True)
class DeleteService:
    repository: ServiceRepository

    async def execute(self, service_id: uuid.UUID) -> None:
        deleted = await self.repository.delete(service_id)
        if not deleted:
            raise ResourceNotFoundError("Service not found")
