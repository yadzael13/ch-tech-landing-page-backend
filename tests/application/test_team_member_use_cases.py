import uuid
from datetime import UTC, datetime

import pytest

from app.application.ports.team_member_repository import TeamMemberInput
from app.application.use_cases.team_members import (
    CreateTeamMember,
    DeleteTeamMember,
    GetTeamMemberById,
    ListTeamMembers,
    UpdateTeamMember,
)
from app.core.errors import ResourceNotFoundError
from app.domain.enums import UserRole
from app.domain.team_member import TeamMember
from app.domain.user import User
from app.domain.value_objects import Email
from tests.application.fakes import InMemoryTeamMemberRepository, InMemoryUserRepository


def _team_member(**overrides: object) -> TeamMember:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "user_id": None,
        "name": "Yadzael Chalico",
        "role": "Founder & Lead Software Engineer",
        "bio": None,
        "photo": None,
        "linkedin_url": None,
        "github_url": None,
        "display_order": 0,
        "active": True,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return TeamMember(**defaults)  # type: ignore[arg-type]


def _user(**overrides: object) -> User:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "name": "Admin",
        "email": Email("admin@ch-tech.dev"),
        "password_hash": "hash",
        "role": UserRole.ADMIN,
        "is_active": True,
        "last_login": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return User(**defaults)  # type: ignore[arg-type]


def _input(**overrides: object) -> TeamMemberInput:
    defaults: dict[str, object] = {
        "user_id": None,
        "name": "New Member",
        "role": "Engineer",
        "bio": None,
    }
    defaults.update(overrides)
    return TeamMemberInput(**defaults)  # type: ignore[arg-type]


async def test_list_team_members_hides_inactive_when_active_only() -> None:
    active = _team_member(active=True, display_order=0)
    inactive = _team_member(active=False, display_order=1)
    repo = InMemoryTeamMemberRepository([active, inactive])
    use_case = ListTeamMembers(repository=repo)

    result = await use_case.execute(active_only=True)

    assert [m.id for m in result] == [active.id]


async def test_list_team_members_includes_inactive_when_not_active_only() -> None:
    active = _team_member(active=True)
    inactive = _team_member(active=False)
    repo = InMemoryTeamMemberRepository([active, inactive])
    use_case = ListTeamMembers(repository=repo)

    result = await use_case.execute(active_only=False)

    assert {m.id for m in result} == {active.id, inactive.id}


async def test_get_team_member_by_id_raises_not_found_when_inactive_and_filtered() -> (
    None
):
    member = _team_member(active=False)
    repo = InMemoryTeamMemberRepository([member])
    use_case = GetTeamMemberById(repository=repo)

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(member.id, active_only=True)


async def test_get_team_member_by_id_succeeds_when_not_filtered() -> None:
    member = _team_member(active=False)
    repo = InMemoryTeamMemberRepository([member])
    use_case = GetTeamMemberById(repository=repo)

    result = await use_case.execute(member.id, active_only=False)

    assert result.id == member.id


async def test_create_team_member_without_a_user_link_succeeds() -> None:
    use_case = CreateTeamMember(
        repository=InMemoryTeamMemberRepository(),
        user_repository=InMemoryUserRepository(),
    )

    result = await use_case.execute(_input())

    assert result.user_id is None


async def test_create_team_member_rejects_an_unknown_user() -> None:
    use_case = CreateTeamMember(
        repository=InMemoryTeamMemberRepository(),
        user_repository=InMemoryUserRepository(),
    )

    with pytest.raises(ResourceNotFoundError, match="User not found"):
        await use_case.execute(_input(user_id=uuid.uuid4()))


async def test_create_team_member_succeeds_for_a_known_user() -> None:
    user = _user()
    use_case = CreateTeamMember(
        repository=InMemoryTeamMemberRepository(),
        user_repository=InMemoryUserRepository([user]),
    )

    result = await use_case.execute(_input(user_id=user.id))

    assert result.user_id == user.id


async def test_update_team_member_raises_not_found_when_missing() -> None:
    use_case = UpdateTeamMember(
        repository=InMemoryTeamMemberRepository(),
        user_repository=InMemoryUserRepository(),
    )

    with pytest.raises(ResourceNotFoundError, match="Team member not found"):
        await use_case.execute(uuid.uuid4(), _input())


async def test_delete_team_member_raises_not_found_when_missing() -> None:
    use_case = DeleteTeamMember(repository=InMemoryTeamMemberRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_delete_team_member_removes_it() -> None:
    member = _team_member()
    repo = InMemoryTeamMemberRepository([member])
    use_case = DeleteTeamMember(repository=repo)

    await use_case.execute(member.id)

    assert await repo.get_by_id(member.id, active_only=False) is None
