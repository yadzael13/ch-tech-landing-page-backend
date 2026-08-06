"""TechnologyRepository port (ADR-0012, ARCHITECTURE.md, Fase 4)."""

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.domain.technology import Technology


@dataclass(slots=True)
class TechnologyFilters:
    category: str | None = None


@dataclass(slots=True)
class TechnologyInput:
    name: str
    category: str | None = None
    icon: str | None = None
    official_url: str | None = None


class TechnologyRepository(Protocol):
    async def list(self, filters: TechnologyFilters) -> list[Technology]: ...

    async def get_by_id(self, technology_id: uuid.UUID) -> Technology | None: ...

    async def create(self, data: TechnologyInput) -> Technology: ...

    async def update(
        self, technology_id: uuid.UUID, data: TechnologyInput
    ) -> Technology | None: ...

    async def delete(self, technology_id: uuid.UUID) -> bool: ...
