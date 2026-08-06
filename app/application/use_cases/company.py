"""Company use cases (ADR-0012, Fase 6)."""

from dataclasses import dataclass

from app.application.ports.company_repository import CompanyInput, CompanyRepository
from app.core.errors import ResourceNotFoundError
from app.domain.company import Company


@dataclass(slots=True)
class GetCompany:
    repository: CompanyRepository

    async def execute(self) -> Company:
        result = await self.repository.get()
        if result is None:
            raise ResourceNotFoundError("Company profile not found")
        return result


@dataclass(slots=True)
class UpdateCompany:
    repository: CompanyRepository

    async def execute(self, data: CompanyInput) -> Company:
        return await self.repository.update(data)
