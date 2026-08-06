"""ServiceRepository port (ADR-0012, ARCHITECTURE.md, Fase 4)."""

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.domain.service import Service


@dataclass(slots=True)
class ServiceInput:
    slug: str
    title: str
    description: str | None
    featured: bool
    active: bool


class ServiceRepository(Protocol):
    async def list(self, *, active_only: bool) -> list[Service]: ...

    async def get_by_slug(self, slug: str, *, active_only: bool) -> Service | None: ...

    async def get_by_id(self, service_id: uuid.UUID) -> Service | None: ...

    async def create(self, data: ServiceInput) -> Service: ...

    async def update(
        self, service_id: uuid.UUID, data: ServiceInput
    ) -> Service | None: ...

    async def delete(self, service_id: uuid.UUID) -> bool: ...
