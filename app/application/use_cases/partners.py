"""Partner use cases (ADR-0012, Fase 6)."""

import uuid
from dataclasses import dataclass

from app.application.ports.partner_repository import PartnerInput, PartnerRepository
from app.core.errors import ResourceNotFoundError
from app.domain.partner import Partner


@dataclass(slots=True)
class ListPartners:
    repository: PartnerRepository

    async def execute(self) -> list[Partner]:
        return await self.repository.list()


@dataclass(slots=True)
class CreatePartner:
    repository: PartnerRepository

    async def execute(self, data: PartnerInput) -> Partner:
        return await self.repository.create(data)


@dataclass(slots=True)
class UpdatePartner:
    repository: PartnerRepository

    async def execute(self, partner_id: uuid.UUID, data: PartnerInput) -> Partner:
        result = await self.repository.update(partner_id, data)
        if result is None:
            raise ResourceNotFoundError("Partner not found")
        return result


@dataclass(slots=True)
class DeletePartner:
    repository: PartnerRepository

    async def execute(self, partner_id: uuid.UUID) -> None:
        deleted = await self.repository.delete(partner_id)
        if not deleted:
            raise ResourceNotFoundError("Partner not found")
