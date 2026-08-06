import uuid
from datetime import UTC, datetime

import pytest

from app.application.ports.service_repository import ServiceInput
from app.application.use_cases.services import (
    CreateService,
    DeleteService,
    GetServiceById,
    GetServiceBySlug,
    ListServices,
    UpdateService,
)
from app.core.errors import ConflictError, ResourceNotFoundError
from app.domain.service import Service
from app.domain.value_objects import Slug
from tests.application.fakes import InMemoryServiceRepository


def _service(**overrides: object) -> Service:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "service_line_id": None,
        "title": "Automatización con IA",
        "slug": Slug("automatizacion-ia"),
        "description": None,
        "featured": False,
        "active": True,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Service(**defaults)  # type: ignore[arg-type]


def _input(**overrides: object) -> ServiceInput:
    defaults: dict[str, object] = {
        "slug": "new-service",
        "title": "New Service",
        "description": None,
        "featured": False,
        "active": True,
    }
    defaults.update(overrides)
    return ServiceInput(**defaults)  # type: ignore[arg-type]


async def test_list_services_hides_inactive_when_active_only() -> None:
    active = _service(active=True)
    inactive = _service(active=False)
    repo = InMemoryServiceRepository([active, inactive])
    use_case = ListServices(repository=repo)

    result = await use_case.execute(active_only=True)

    assert [s.id for s in result] == [active.id]


async def test_get_service_by_slug_raises_not_found_when_missing() -> None:
    use_case = GetServiceBySlug(repository=InMemoryServiceRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute("missing", active_only=True)


async def test_get_service_by_id_raises_not_found_when_missing() -> None:
    use_case = GetServiceById(repository=InMemoryServiceRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_create_service_persists_it() -> None:
    repo = InMemoryServiceRepository()
    use_case = CreateService(repository=repo)

    result = await use_case.execute(_input(slug="brand-new"))

    assert str(result.slug) == "brand-new"


async def test_create_service_rejects_a_duplicate_slug() -> None:
    repo = InMemoryServiceRepository([_service(slug=Slug("taken"))])
    use_case = CreateService(repository=repo)

    with pytest.raises(ConflictError):
        await use_case.execute(_input(slug="taken"))


async def test_update_service_raises_not_found_when_missing() -> None:
    use_case = UpdateService(repository=InMemoryServiceRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4(), _input())


async def test_update_service_applies_changes() -> None:
    service = _service(title="Old Title")
    repo = InMemoryServiceRepository([service])
    use_case = UpdateService(repository=repo)

    result = await use_case.execute(
        service.id, _input(slug=str(service.slug), title="New Title")
    )

    assert result.title == "New Title"


async def test_delete_service_raises_not_found_when_missing() -> None:
    use_case = DeleteService(repository=InMemoryServiceRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_delete_service_removes_it() -> None:
    service = _service()
    repo = InMemoryServiceRepository([service])
    use_case = DeleteService(repository=repo)

    await use_case.execute(service.id)

    assert await repo.get_by_id(service.id) is None
