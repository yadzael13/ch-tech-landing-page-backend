import uuid
from datetime import UTC, datetime

import pytest

from app.application.ports.service_line_repository import ServiceLineInput
from app.application.use_cases.service_lines import (
    CreateServiceLine,
    DeleteServiceLine,
    GetServiceLineBySlug,
    ListServiceLines,
    UpdateServiceLine,
)
from app.core.errors import ConflictError, ResourceNotFoundError
from app.domain.service_line import ServiceLine
from app.domain.value_objects import Slug
from tests.application.fakes import InMemoryServiceLineRepository


def _service_line(**overrides: object) -> ServiceLine:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "slug": Slug("software-engineering"),
        "name": "Software Engineering",
        "description": None,
        "icon": None,
        "display_order": 0,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return ServiceLine(**defaults)  # type: ignore[arg-type]


def _input(**overrides: object) -> ServiceLineInput:
    defaults: dict[str, object] = {
        "slug": "new-line",
        "name": "New Line",
        "description": None,
    }
    defaults.update(overrides)
    return ServiceLineInput(**defaults)  # type: ignore[arg-type]


async def test_list_service_lines_sorted_by_display_order() -> None:
    second = _service_line(slug=Slug("second"), display_order=1)
    first = _service_line(slug=Slug("first"), display_order=0)
    repo = InMemoryServiceLineRepository([second, first])
    use_case = ListServiceLines(repository=repo)

    result = await use_case.execute()

    assert [str(r.slug) for r in result] == ["first", "second"]


async def test_get_service_line_by_slug_raises_not_found_when_missing() -> None:
    use_case = GetServiceLineBySlug(repository=InMemoryServiceLineRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute("missing")


async def test_create_service_line_persists_it() -> None:
    repo = InMemoryServiceLineRepository()
    use_case = CreateServiceLine(repository=repo)

    result = await use_case.execute(_input(slug="ai-automation"))

    assert str(result.slug) == "ai-automation"


async def test_create_service_line_rejects_a_duplicate_slug() -> None:
    repo = InMemoryServiceLineRepository([_service_line(slug=Slug("taken"))])
    use_case = CreateServiceLine(repository=repo)

    with pytest.raises(ConflictError):
        await use_case.execute(_input(slug="taken"))


async def test_update_service_line_raises_not_found_when_missing() -> None:
    use_case = UpdateServiceLine(repository=InMemoryServiceLineRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4(), _input())


async def test_delete_service_line_raises_not_found_when_missing() -> None:
    use_case = DeleteServiceLine(repository=InMemoryServiceLineRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_delete_service_line_removes_it() -> None:
    line = _service_line()
    repo = InMemoryServiceLineRepository([line])
    use_case = DeleteServiceLine(repository=repo)

    await use_case.execute(line.id)

    assert await repo.get_by_slug(str(line.slug)) is None
