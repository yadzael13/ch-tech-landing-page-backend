import uuid
from datetime import UTC, datetime

import pytest

from app.application.ports.company_repository import CompanyInput
from app.application.use_cases.company import GetCompany, UpdateCompany
from app.core.errors import ResourceNotFoundError
from app.domain.company import Company
from tests.application.fakes import InMemoryCompanyRepository


def _company(**overrides: object) -> Company:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "legal_name": "CH-TECH",
        "display_name": "CH-TECH",
        "tagline": None,
        "mission": None,
        "vision": None,
        "email": None,
        "phone": None,
        "address": None,
        "social_links": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Company(**defaults)  # type: ignore[arg-type]


def _input(**overrides: object) -> CompanyInput:
    defaults: dict[str, object] = {
        "legal_name": "CH-TECH",
        "display_name": "CH-TECH",
        "tagline": None,
        "mission": None,
        "vision": None,
    }
    defaults.update(overrides)
    return CompanyInput(**defaults)  # type: ignore[arg-type]


async def test_get_company_raises_not_found_when_never_seeded() -> None:
    use_case = GetCompany(repository=InMemoryCompanyRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute()


async def test_get_company_returns_the_singleton() -> None:
    company = _company(display_name="CH-TECH")
    use_case = GetCompany(repository=InMemoryCompanyRepository(company))

    result = await use_case.execute()

    assert result.display_name == "CH-TECH"


async def test_update_company_creates_it_when_missing() -> None:
    use_case = UpdateCompany(repository=InMemoryCompanyRepository())

    result = await use_case.execute(_input(tagline="New tagline"))

    assert result.tagline == "New tagline"


async def test_update_company_replaces_the_existing_singleton() -> None:
    company = _company(tagline="Old tagline")
    repo = InMemoryCompanyRepository(company)
    use_case = UpdateCompany(repository=repo)

    result = await use_case.execute(_input(tagline="New tagline"))

    assert result.id == company.id
    assert result.tagline == "New tagline"
