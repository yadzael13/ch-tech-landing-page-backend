import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.testimonial_repository import TestimonialInput
from app.infrastructure.repositories.testimonial_repository import (
    SQLAlchemyTestimonialRepository,
)
from app.models import Client as ClientModel
from app.models import Project as ProjectModel


def _input(**overrides: object) -> TestimonialInput:
    defaults: dict[str, object] = {
        "author_name": "Ada Lovelace",
        "author_role": "CTO",
        "client_id": None,
        "project_id": None,
        "content": "Great work.",
        "rating": None,
        "featured": False,
    }
    defaults.update(overrides)
    return TestimonialInput(**defaults)  # type: ignore[arg-type]


async def test_create_persists_and_returns_the_testimonial(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyTestimonialRepository(db_session)

    result = await repo.create(_input())

    assert result.author_name == "Ada Lovelace"
    assert result.id is not None


async def test_create_with_client_and_project_references(
    db_session: AsyncSession,
) -> None:
    client = ClientModel(name="Acme Corp")
    project = ProjectModel(slug="sample", title="Sample", visibility="PUBLIC")
    db_session.add_all([client, project])
    await db_session.flush()

    repo = SQLAlchemyTestimonialRepository(db_session)
    result = await repo.create(_input(client_id=client.id, project_id=project.id))

    assert result.client_id == client.id
    assert result.project_id == project.id


async def test_list_sorted_by_created_at(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTestimonialRepository(db_session)
    first = await repo.create(_input(author_name="First"))
    second = await repo.create(_input(author_name="Second"))

    result = await repo.list()

    assert [r.id for r in result] == [first.id, second.id]


async def test_update_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTestimonialRepository(db_session)
    assert await repo.update(uuid.uuid4(), _input()) is None


async def test_update_applies_changes(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTestimonialRepository(db_session)
    created = await repo.create(_input(content="Old content"))

    updated = await repo.update(created.id, _input(content="New content"))

    assert updated is not None
    assert updated.content == "New content"


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTestimonialRepository(db_session)
    assert await repo.delete(uuid.uuid4()) is False


async def test_delete_removes_the_testimonial(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTestimonialRepository(db_session)
    created = await repo.create(_input())

    assert await repo.delete(created.id) is True
    assert created.id not in {t.id for t in await repo.list()}
