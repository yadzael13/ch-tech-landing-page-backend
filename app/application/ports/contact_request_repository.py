"""ContactRequestRepository port (ADR-0012, ARCHITECTURE.md, Fase 4)."""

from dataclasses import dataclass
from typing import Protocol

from app.domain.contact_request import ContactRequest


@dataclass(slots=True)
class ContactRequestInput:
    name: str
    email: str
    company: str | None
    subject: str | None
    message: str


class ContactRequestRepository(Protocol):
    async def create(self, data: ContactRequestInput) -> ContactRequest: ...
