import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.application.ports.team_member_repository import TeamMemberInput
from app.application.use_cases.team_members import (
    CreateTeamMember,
    DeleteTeamMember,
    GetTeamMemberById,
    ListTeamMembers,
    UpdateTeamMember,
)
from app.core.rate_limit import ip_rate_limiter
from app.db.session import get_db
from app.domain.team_member import TeamMember
from app.infrastructure.repositories.team_member_repository import (
    SQLAlchemyTeamMemberRepository,
)
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.schemas.response import SuccessResponse
from app.schemas.team_member import TeamMemberItem, TeamMemberWrite

public_router = APIRouter(prefix="/team", tags=["team"])
admin_router = APIRouter(prefix="/admin/team", tags=["admin:team"])

# API.md "Rate Limiting" -> "API Pública": 100 requests/minute/IP.
_public_api_limit = Depends(
    ip_rate_limiter(limit=100, window_seconds=60, scope="public-api")
)

# Admin writes are auth-gated but otherwise had no throttle — a leaked
# access token could hammer these without limit (OWASP API4:2023).
_admin_write_limit = Depends(
    ip_rate_limiter(limit=60, window_seconds=60, scope="admin-write")
)


def _list_use_case(session: AsyncSession = Depends(get_db)) -> ListTeamMembers:
    return ListTeamMembers(repository=SQLAlchemyTeamMemberRepository(session))


def _get_by_id_use_case(
    session: AsyncSession = Depends(get_db),
) -> GetTeamMemberById:
    return GetTeamMemberById(repository=SQLAlchemyTeamMemberRepository(session))


def _create_use_case(session: AsyncSession = Depends(get_db)) -> CreateTeamMember:
    return CreateTeamMember(
        repository=SQLAlchemyTeamMemberRepository(session),
        user_repository=SQLAlchemyUserRepository(session),
    )


def _update_use_case(session: AsyncSession = Depends(get_db)) -> UpdateTeamMember:
    return UpdateTeamMember(
        repository=SQLAlchemyTeamMemberRepository(session),
        user_repository=SQLAlchemyUserRepository(session),
    )


def _delete_use_case(session: AsyncSession = Depends(get_db)) -> DeleteTeamMember:
    return DeleteTeamMember(repository=SQLAlchemyTeamMemberRepository(session))


def _to_item(member: TeamMember) -> TeamMemberItem:
    return TeamMemberItem(
        id=member.id,
        user_id=member.user_id,
        name=member.name,
        role=member.role,
        bio=member.bio,
        photo=str(member.photo) if member.photo else None,
        linkedin_url=str(member.linkedin_url) if member.linkedin_url else None,
        github_url=str(member.github_url) if member.github_url else None,
        display_order=member.display_order,
        active=member.active,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


def _to_input(payload: TeamMemberWrite) -> TeamMemberInput:
    return TeamMemberInput(
        user_id=payload.user_id,
        name=payload.name,
        role=payload.role,
        bio=payload.bio,
        photo=payload.photo,
        linkedin_url=payload.linkedin_url,
        github_url=payload.github_url,
        display_order=payload.display_order,
        active=payload.active,
    )


@public_router.get("", dependencies=[_public_api_limit])
async def list_team_members(
    use_case: ListTeamMembers = Depends(_list_use_case),
) -> SuccessResponse[list[TeamMemberItem]]:
    members = await use_case.execute(active_only=True)
    return SuccessResponse(data=[_to_item(m) for m in members])


@public_router.get("/{team_member_id}", dependencies=[_public_api_limit])
async def get_team_member(
    team_member_id: uuid.UUID,
    use_case: GetTeamMemberById = Depends(_get_by_id_use_case),
) -> SuccessResponse[TeamMemberItem]:
    member = await use_case.execute(team_member_id, active_only=True)
    return SuccessResponse(data=_to_item(member))


@admin_router.get("")
async def list_admin_team_members(
    _current_user_id: str = Depends(get_current_user_id),
    use_case: ListTeamMembers = Depends(_list_use_case),
) -> SuccessResponse[list[TeamMemberItem]]:
    """Same shape as GET /team, minus the active=True filter — the admin
    management table needs to see inactive members too."""
    members = await use_case.execute(active_only=False)
    return SuccessResponse(data=[_to_item(m) for m in members])


@admin_router.get("/{team_member_id}")
async def get_admin_team_member(
    team_member_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: GetTeamMemberById = Depends(_get_by_id_use_case),
) -> SuccessResponse[TeamMemberItem]:
    """Same shape as GET /team/{id}, but without the active=True filter —
    lets the edit form load an inactive member the public endpoint would
    404 on."""
    member = await use_case.execute(team_member_id, active_only=False)
    return SuccessResponse(data=_to_item(member))


@admin_router.post("", status_code=201, dependencies=[_admin_write_limit])
async def create_team_member(
    payload: TeamMemberWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: CreateTeamMember = Depends(_create_use_case),
) -> SuccessResponse[TeamMemberItem]:
    member = await use_case.execute(_to_input(payload))
    return SuccessResponse(data=_to_item(member))


@admin_router.put("/{team_member_id}", dependencies=[_admin_write_limit])
async def update_team_member(
    team_member_id: uuid.UUID,
    payload: TeamMemberWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: UpdateTeamMember = Depends(_update_use_case),
) -> SuccessResponse[TeamMemberItem]:
    member = await use_case.execute(team_member_id, _to_input(payload))
    return SuccessResponse(data=_to_item(member))


@admin_router.delete(
    "/{team_member_id}", status_code=204, dependencies=[_admin_write_limit]
)
async def delete_team_member(
    team_member_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: DeleteTeamMember = Depends(_delete_use_case),
) -> None:
    await use_case.execute(team_member_id)
