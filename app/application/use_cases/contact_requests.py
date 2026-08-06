"""ContactRequest use cases (ADR-0012, Fase 4)."""

from dataclasses import dataclass

from app.application.ports.contact_request_repository import (
    ContactRequestInput,
    ContactRequestRepository,
)
from app.domain.contact_request import ContactRequest


@dataclass(slots=True)
class SubmitContactRequest:
    repository: ContactRequestRepository

    async def execute(self, data: ContactRequestInput) -> ContactRequest:
        return await self.repository.create(data)
