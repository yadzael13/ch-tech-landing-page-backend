import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.partner_repository import PartnerInput
from app.infrastructure.repositories.partner_repository import (
    SQLAlchemyPartnerRepository,
)


def _input(**overrides: object) -> PartnerInput:
    defaults: dict[str, object] = {"name": "Amazon Web Services"}
    defaults.update(overrides)
    return PartnerInput(**defaults)  # type: ignore[arg-type]


async def test_create_persists_and_returns_the_partner(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyPartnerRepository(db_session)

    result = await repo.create(_input(name="Brand New"))

    assert result.name == "Brand New"


async def test_list_sorted_by_name(db_session: AsyncSession) -> None:
    repo = SQLAlchemyPartnerRepository(db_session)
    await repo.create(_input(name="Zeta Cloud"))
    await repo.create(_input(name="Amazon Web Services"))

    result = await repo.list()

    assert [p.name for p in result] == ["Amazon Web Services", "Zeta Cloud"]


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyPartnerRepository(db_session)
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_update_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyPartnerRepository(db_session)
    assert await repo.update(uuid.uuid4(), _input()) is None


async def test_update_applies_changes(db_session: AsyncSession) -> None:
    repo = SQLAlchemyPartnerRepository(db_session)
    created = await repo.create(_input(name="Old Name"))

    updated = await repo.update(created.id, _input(name="New Name"))

    assert updated is not None
    assert updated.name == "New Name"


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyPartnerRepository(db_session)
    assert await repo.delete(uuid.uuid4()) is False


async def test_delete_removes_the_partner(db_session: AsyncSession) -> None:
    repo = SQLAlchemyPartnerRepository(db_session)
    created = await repo.create(_input())

    assert await repo.delete(created.id) is True
    assert await repo.get_by_id(created.id) is None
