import uuid
from datetime import UTC, datetime

import pytest

from app.application.ports.technology_repository import (
    TechnologyFilters,
    TechnologyInput,
)
from app.application.use_cases.technologies import (
    CreateTechnology,
    DeleteTechnology,
    GetTechnologyById,
    ListTechnologies,
    UpdateTechnology,
)
from app.core.errors import ResourceNotFoundError
from app.domain.technology import Technology
from tests.application.fakes import InMemoryTechnologyRepository


def _technology(**overrides: object) -> Technology:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "name": "FastAPI",
        "category": "Backend",
        "icon": None,
        "official_url": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Technology(**defaults)  # type: ignore[arg-type]


def _input(**overrides: object) -> TechnologyInput:
    defaults: dict[str, object] = {"name": "Docker", "category": "Infra"}
    defaults.update(overrides)
    return TechnologyInput(**defaults)  # type: ignore[arg-type]


async def test_list_technologies_filters_by_category() -> None:
    backend = _technology(category="Backend")
    infra = _technology(category="Infra")
    repo = InMemoryTechnologyRepository([backend, infra])
    use_case = ListTechnologies(repository=repo)

    result = await use_case.execute(TechnologyFilters(category="Infra"))

    assert [t.id for t in result] == [infra.id]


async def test_get_technology_by_id_raises_not_found_when_missing() -> None:
    use_case = GetTechnologyById(repository=InMemoryTechnologyRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_create_technology_persists_it() -> None:
    repo = InMemoryTechnologyRepository()
    use_case = CreateTechnology(repository=repo)

    result = await use_case.execute(_input(name="Redis"))

    assert result.name == "Redis"
    assert await repo.get_by_id(result.id) is not None


async def test_update_technology_raises_not_found_when_missing() -> None:
    use_case = UpdateTechnology(repository=InMemoryTechnologyRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4(), _input())


async def test_update_technology_applies_changes() -> None:
    tech = _technology(name="Old Name")
    repo = InMemoryTechnologyRepository([tech])
    use_case = UpdateTechnology(repository=repo)

    result = await use_case.execute(tech.id, _input(name="New Name"))

    assert result.name == "New Name"


async def test_delete_technology_raises_not_found_when_missing() -> None:
    use_case = DeleteTechnology(repository=InMemoryTechnologyRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_delete_technology_removes_it() -> None:
    tech = _technology()
    repo = InMemoryTechnologyRepository([tech])
    use_case = DeleteTechnology(repository=repo)

    await use_case.execute(tech.id)

    assert await repo.get_by_id(tech.id) is None
