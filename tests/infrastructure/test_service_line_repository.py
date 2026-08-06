import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.service_line_repository import ServiceLineInput
from app.core.errors import ConflictError
from app.infrastructure.repositories.service_line_repository import (
    SQLAlchemyServiceLineRepository,
)
from app.models import Service as ServiceModel


def _input(**overrides: object) -> ServiceLineInput:
    defaults: dict[str, object] = {
        "slug": "repo-test",
        "name": "Repo Test",
        "description": None,
    }
    defaults.update(overrides)
    return ServiceLineInput(**defaults)  # type: ignore[arg-type]


async def test_create_persists_and_returns_the_service_line(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyServiceLineRepository(db_session)

    result = await repo.create(_input(slug="brand-new"))

    assert str(result.slug) == "brand-new"


async def test_create_rejects_a_duplicate_slug(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceLineRepository(db_session)
    await repo.create(_input(slug="taken"))

    with pytest.raises(ConflictError):
        await repo.create(_input(slug="taken"))


async def test_list_sorted_by_display_order(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceLineRepository(db_session)
    await repo.create(_input(slug="second", display_order=1))
    await repo.create(_input(slug="first", display_order=0))

    result = await repo.list()

    assert [str(r.slug) for r in result] == ["first", "second"]


async def test_get_by_slug_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceLineRepository(db_session)
    assert await repo.get_by_slug("missing") is None


async def test_update_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceLineRepository(db_session)
    assert await repo.update(uuid.uuid4(), _input()) is None


async def test_update_applies_changes(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceLineRepository(db_session)
    created = await repo.create(_input(slug="to-update", name="Old Name"))

    updated = await repo.update(created.id, _input(slug="to-update", name="New Name"))

    assert updated is not None
    assert updated.name == "New Name"


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceLineRepository(db_session)
    assert await repo.delete(uuid.uuid4()) is False


async def test_delete_removes_the_service_line(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceLineRepository(db_session)
    created = await repo.create(_input(slug="to-delete"))

    assert await repo.delete(created.id) is True
    assert await repo.get_by_slug("to-delete") is None


async def test_delete_raises_conflict_when_referenced_by_a_service(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyServiceLineRepository(db_session)
    created = await repo.create(_input(slug="has-service"))

    db_session.add(
        ServiceModel(title="Dependent", slug="dependent", service_line_id=created.id)
    )
    await db_session.commit()

    with pytest.raises(ConflictError):
        await repo.delete(created.id)
