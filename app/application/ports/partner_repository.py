"""PartnerRepository port (ADR-0012, ARCHITECTURE.md, Fase 6)."""

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.domain.partner import Partner


@dataclass(slots=True)
class PartnerInput:
    name: str
    logo: str | None = None
    partnership_type: str | None = None
    website_url: str | None = None


class PartnerRepository(Protocol):
    async def list(self) -> list[Partner]: ...

    async def get_by_id(self, partner_id: uuid.UUID) -> Partner | None: ...

    async def create(self, data: PartnerInput) -> Partner: ...

    async def update(
        self, partner_id: uuid.UUID, data: PartnerInput
    ) -> Partner | None: ...

    async def delete(self, partner_id: uuid.UUID) -> bool: ...
