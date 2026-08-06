import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.client_repository import ClientInput
from app.core.errors import ConflictError
from app.infrastructure.repositories.client_repository import (
    SQLAlchemyClientRepository,
)
from app.models import Project as ProjectModel


def _input(**overrides: object) -> ClientInput:
    defaults: dict[str, object] = {"name": "Acme Corp"}
    defaults.update(overrides)
    return ClientInput(**defaults)  # type: ignore[arg-type]


async def test_create_persists_and_returns_the_client(db_session: AsyncSession) -> None:
    repo = SQLAlchemyClientRepository(db_session)

    result = await repo.create(_input(name="Brand New"))

    assert result.name == "Brand New"


async def test_list_sorted_by_name(db_session: AsyncSession) -> None:
    repo = SQLAlchemyClientRepository(db_session)
    await repo.create(_input(name="Zeta Inc"))
    await repo.create(_input(name="Acme Corp"))

    result = await repo.list()

    assert [c.name for c in result] == ["Acme Corp", "Zeta Inc"]


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyClientRepository(db_session)
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_update_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyClientRepository(db_session)
    assert await repo.update(uuid.uuid4(), _input()) is None


async def test_update_applies_changes(db_session: AsyncSession) -> None:
    repo = SQLAlchemyClientRepository(db_session)
    created = await repo.create(_input(name="Old Name"))

    updated = await repo.update(created.id, _input(name="New Name"))

    assert updated is not None
    assert updated.name == "New Name"


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyClientRepository(db_session)
    assert await repo.delete(uuid.uuid4()) is False


async def test_delete_removes_the_client(db_session: AsyncSession) -> None:
    repo = SQLAlchemyClientRepository(db_session)
    created = await repo.create(_input())

    assert await repo.delete(created.id) is True
    assert await repo.get_by_id(created.id) is None


async def test_delete_raises_conflict_when_referenced_by_a_project(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyClientRepository(db_session)
    created = await repo.create(_input(name="Has Project"))

    db_session.add(
        ProjectModel(slug="client-project", title="Client Project", client_id=created.id)
    )
    await db_session.commit()

    with pytest.raises(ConflictError):
        await repo.delete(created.id)


async def test_round_trip_preserves_logo_and_website_url(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyClientRepository(db_session)
    created = await repo.create(
        _input(
            logo="https://ch-tech.dev/clients/acme.png",
            website_url="https://acme.example.com",
        )
    )

    fetched = await repo.get_by_id(created.id)

    assert fetched is not None
    assert str(fetched.logo) == "https://ch-tech.dev/clients/acme.png"
    assert str(fetched.website_url) == "https://acme.example.com"
