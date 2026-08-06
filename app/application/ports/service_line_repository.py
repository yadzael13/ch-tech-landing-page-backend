"""ServiceLineRepository port (ADR-0012, ARCHITECTURE.md, Fase 6)."""

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.domain.service_line import ServiceLine


@dataclass(slots=True)
class ServiceLineInput:
    slug: str
    name: str
    description: str | None
    icon: str | None = None
    display_order: int = 0


class ServiceLineRepository(Protocol):
    async def list(self) -> list[ServiceLine]: ...

    async def get_by_slug(self, slug: str) -> ServiceLine | None: ...

    async def create(self, data: ServiceLineInput) -> ServiceLine: ...

    async def update(
        self, service_line_id: uuid.UUID, data: ServiceLineInput
    ) -> ServiceLine | None: ...

    async def delete(self, service_line_id: uuid.UUID) -> bool: ...
