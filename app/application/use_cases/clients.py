"""Client use cases (ADR-0012, Fase 6)."""

import uuid
from dataclasses import dataclass

from app.application.ports.client_repository import ClientInput, ClientRepository
from app.core.errors import ResourceNotFoundError
from app.domain.client import Client


@dataclass(slots=True)
class ListClients:
    repository: ClientRepository

    async def execute(self) -> list[Client]:
        return await self.repository.list()


@dataclass(slots=True)
class CreateClient:
    repository: ClientRepository

    async def execute(self, data: ClientInput) -> Client:
        return await self.repository.create(data)


@dataclass(slots=True)
class UpdateClient:
    repository: ClientRepository

    async def execute(self, client_id: uuid.UUID, data: ClientInput) -> Client:
        result = await self.repository.update(client_id, data)
        if result is None:
            raise ResourceNotFoundError("Client not found")
        return result


@dataclass(slots=True)
class DeleteClient:
    repository: ClientRepository

    async def execute(self, client_id: uuid.UUID) -> None:
        deleted = await self.repository.delete(client_id)
        if not deleted:
            raise ResourceNotFoundError("Client not found")
