import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.service_repository import ServiceInput
from app.core.errors import ConflictError
from app.infrastructure.repositories.service_repository import (
    SQLAlchemyServiceRepository,
)


def _input(**overrides: object) -> ServiceInput:
    defaults: dict[str, object] = {
        "slug": "repo-test",
        "title": "Repo Test",
        "description": None,
        "featured": False,
        "active": True,
    }
    defaults.update(overrides)
    return ServiceInput(**defaults)  # type: ignore[arg-type]


async def test_create_persists_and_returns_the_service(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyServiceRepository(db_session)

    result = await repo.create(_input(slug="brand-new"))

    assert str(result.slug) == "brand-new"


async def test_create_rejects_a_duplicate_slug(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceRepository(db_session)
    await repo.create(_input(slug="taken"))

    with pytest.raises(ConflictError):
        await repo.create(_input(slug="taken"))


async def test_list_hides_inactive_when_active_only(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceRepository(db_session)
    await repo.create(_input(slug="active-one", active=True))
    await repo.create(_input(slug="inactive-one", active=False))

    result = await repo.list(active_only=True)

    assert [str(s.slug) for s in result] == ["active-one"]


async def test_get_by_slug_hides_inactive_when_active_only(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyServiceRepository(db_session)
    await repo.create(_input(slug="inactive-one", active=False))

    assert await repo.get_by_slug("inactive-one", active_only=True) is None
    found = await repo.get_by_slug("inactive-one", active_only=False)
    assert found is not None


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceRepository(db_session)
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_update_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceRepository(db_session)
    assert await repo.update(uuid.uuid4(), _input()) is None


async def test_update_applies_changes(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceRepository(db_session)
    created = await repo.create(_input(slug="to-update", title="Old Title"))

    updated = await repo.update(created.id, _input(slug="to-update", title="New Title"))

    assert updated is not None
    assert updated.title == "New Title"


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceRepository(db_session)
    assert await repo.delete(uuid.uuid4()) is False


async def test_delete_removes_the_service(db_session: AsyncSession) -> None:
    repo = SQLAlchemyServiceRepository(db_session)
    created = await repo.create(_input(slug="to-delete"))

    assert await repo.delete(created.id) is True
    assert await repo.get_by_id(created.id) is None
