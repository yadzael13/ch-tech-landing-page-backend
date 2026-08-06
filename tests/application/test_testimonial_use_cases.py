import uuid
from datetime import UTC, datetime

import pytest

from app.application.ports.client_repository import ClientInput
from app.application.ports.testimonial_repository import TestimonialInput
from app.application.use_cases.testimonials import (
    CreateTestimonial,
    DeleteTestimonial,
    ListTestimonials,
    UpdateTestimonial,
)
from app.core.errors import ResourceNotFoundError
from app.domain.testimonial import Testimonial
from tests.application.fakes import (
    InMemoryClientRepository,
    InMemoryProjectRepository,
    InMemoryTestimonialRepository,
)


def _testimonial(**overrides: object) -> Testimonial:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "author_name": "Ada Lovelace",
        "author_role": None,
        "client_id": None,
        "project_id": None,
        "content": "Great work.",
        "rating": None,
        "featured": False,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Testimonial(**defaults)  # type: ignore[arg-type]


def _input(**overrides: object) -> TestimonialInput:
    defaults: dict[str, object] = {
        "author_name": "New Author",
        "author_role": None,
        "client_id": None,
        "project_id": None,
        "content": "Great work.",
        "rating": None,
        "featured": False,
    }
    defaults.update(overrides)
    return TestimonialInput(**defaults)  # type: ignore[arg-type]


def _use_case_deps() -> dict[str, object]:
    return {
        "repository": InMemoryTestimonialRepository(),
        "client_repository": InMemoryClientRepository(),
        "project_repository": InMemoryProjectRepository(),
    }


async def test_list_testimonials_sorted_by_created_at() -> None:
    older = _testimonial(created_at=datetime(2026, 1, 1, tzinfo=UTC))
    newer = _testimonial(created_at=datetime(2026, 2, 1, tzinfo=UTC))
    repo = InMemoryTestimonialRepository([newer, older])
    use_case = ListTestimonials(repository=repo)

    result = await use_case.execute()

    assert [t.id for t in result] == [older.id, newer.id]


async def test_create_testimonial_without_references_succeeds() -> None:
    use_case = CreateTestimonial(**_use_case_deps())  # type: ignore[arg-type]

    result = await use_case.execute(_input())

    assert result.author_name == "New Author"


async def test_create_testimonial_rejects_an_unknown_client() -> None:
    use_case = CreateTestimonial(**_use_case_deps())  # type: ignore[arg-type]

    with pytest.raises(ResourceNotFoundError, match="Client not found"):
        await use_case.execute(_input(client_id=uuid.uuid4()))


async def test_create_testimonial_rejects_an_unknown_project() -> None:
    use_case = CreateTestimonial(**_use_case_deps())  # type: ignore[arg-type]

    with pytest.raises(ResourceNotFoundError, match="Project not found"):
        await use_case.execute(_input(project_id=uuid.uuid4()))


async def test_create_testimonial_succeeds_for_a_known_client() -> None:
    client_repository = InMemoryClientRepository()
    client = await client_repository.create(ClientInput(name="Acme Corp"))
    use_case = CreateTestimonial(
        repository=InMemoryTestimonialRepository(),
        client_repository=client_repository,
        project_repository=InMemoryProjectRepository(),
    )

    result = await use_case.execute(_input(client_id=client.id))

    assert result.client_id == client.id


async def test_update_testimonial_raises_not_found_when_missing() -> None:
    use_case = UpdateTestimonial(**_use_case_deps())  # type: ignore[arg-type]

    with pytest.raises(ResourceNotFoundError, match="Testimonial not found"):
        await use_case.execute(uuid.uuid4(), _input())


async def test_delete_testimonial_raises_not_found_when_missing() -> None:
    use_case = DeleteTestimonial(repository=InMemoryTestimonialRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_delete_testimonial_removes_it() -> None:
    testimonial = _testimonial()
    repo = InMemoryTestimonialRepository([testimonial])
    use_case = DeleteTestimonial(repository=repo)

    await use_case.execute(testimonial.id)

    assert testimonial.id not in {t.id for t in await repo.list()}
