import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.team_member_repository import TeamMemberInput
from app.core.security import hash_password
from app.infrastructure.repositories.team_member_repository import (
    SQLAlchemyTeamMemberRepository,
)
from app.models import User as UserModel


def _input(**overrides: object) -> TeamMemberInput:
    defaults: dict[str, object] = {
        "user_id": None,
        "name": "Yadzael Chalico",
        "role": "Founder & Lead Software Engineer",
        "bio": None,
    }
    defaults.update(overrides)
    return TeamMemberInput(**defaults)  # type: ignore[arg-type]


async def test_create_persists_and_returns_the_team_member(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyTeamMemberRepository(db_session)

    result = await repo.create(_input())

    assert result.name == "Yadzael Chalico"
    assert result.active is True


async def test_create_with_a_user_link(db_session: AsyncSession) -> None:
    user = UserModel(
        name="Admin",
        email=f"{uuid.uuid4()}@ch-tech.dev",
        password_hash=hash_password("x"),
    )
    db_session.add(user)
    await db_session.flush()

    repo = SQLAlchemyTeamMemberRepository(db_session)
    result = await repo.create(_input(user_id=user.id))

    assert result.user_id == user.id


async def test_list_hides_inactive_when_active_only(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTeamMemberRepository(db_session)
    await repo.create(_input(name="Active One", active=True))
    await repo.create(_input(name="Inactive One", active=False))

    result = await repo.list(active_only=True)

    assert [m.name for m in result] == ["Active One"]


async def test_get_by_id_hides_inactive_when_active_only(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyTeamMemberRepository(db_session)
    created = await repo.create(_input(active=False))

    assert await repo.get_by_id(created.id, active_only=True) is None
    found = await repo.get_by_id(created.id, active_only=False)
    assert found is not None


async def test_update_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTeamMemberRepository(db_session)
    assert await repo.update(uuid.uuid4(), _input()) is None


async def test_update_applies_changes(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTeamMemberRepository(db_session)
    created = await repo.create(_input(role="Old Role"))

    updated = await repo.update(created.id, _input(role="New Role"))

    assert updated is not None
    assert updated.role == "New Role"


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTeamMemberRepository(db_session)
    assert await repo.delete(uuid.uuid4()) is False


async def test_delete_removes_the_team_member(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTeamMemberRepository(db_session)
    created = await repo.create(_input())

    assert await repo.delete(created.id) is True
    assert await repo.get_by_id(created.id, active_only=False) is None
