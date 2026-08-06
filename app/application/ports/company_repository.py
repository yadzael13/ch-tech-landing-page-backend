"""CompanyRepository port (ADR-0012, ARCHITECTURE.md, Fase 6).

Company is a singleton (API.md: no POST/DELETE) seeded by app.db.seed.
update() upserts rather than requiring the row to already exist, so a
fresh database that hasn't run the seed yet still behaves correctly.
"""

from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.company import Company


@dataclass(slots=True)
class CompanyInput:
    legal_name: str
    display_name: str
    tagline: str | None
    mission: str | None
    vision: str | None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    social_links: dict[str, Any] | None = None


class CompanyRepository(Protocol):
    async def get(self) -> Company | None: ...

    async def update(self, data: CompanyInput) -> Company: ...
