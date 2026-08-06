"""ClientRepository port (ADR-0012, ARCHITECTURE.md, Fase 6)."""

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.domain.client import Client


@dataclass(slots=True)
class ClientInput:
    name: str
    logo: str | None = None
    industry: str | None = None
    website_url: str | None = None


class ClientRepository(Protocol):
    async def list(self) -> list[Client]: ...

    async def get_by_id(self, client_id: uuid.UUID) -> Client | None: ...

    async def create(self, data: ClientInput) -> Client: ...

    async def update(
        self, client_id: uuid.UUID, data: ClientInput
    ) -> Client | None: ...

    async def delete(self, client_id: uuid.UUID) -> bool: ...
