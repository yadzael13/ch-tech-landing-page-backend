"""TeamMember use cases (ADR-0012, Fase 6).

Create/Update depend on UserRepository too — user_id is optional, but
when supplied must reference a real admin account (same reasoning as
Testimonial's client_id/project_id, CaseStudy's project_id).
"""

import uuid
from dataclasses import dataclass

from app.application.ports.team_member_repository import (
    TeamMemberInput,
    TeamMemberRepository,
)
from app.application.ports.user_repository import UserRepository
from app.core.errors import ResourceNotFoundError
from app.domain.team_member import TeamMember


@dataclass(slots=True)
class ListTeamMembers:
    repository: TeamMemberRepository

    async def execute(self, *, active_only: bool) -> list[TeamMember]:
        return await self.repository.list(active_only=active_only)


@dataclass(slots=True)
class GetTeamMemberById:
    repository: TeamMemberRepository

    async def execute(
        self, team_member_id: uuid.UUID, *, active_only: bool
    ) -> TeamMember:
        result = await self.repository.get_by_id(
            team_member_id, active_only=active_only
        )
        if result is None:
            raise ResourceNotFoundError("Team member not found")
        return result


@dataclass(slots=True)
class CreateTeamMember:
    repository: TeamMemberRepository
    user_repository: UserRepository

    async def execute(self, data: TeamMemberInput) -> TeamMember:
        if (
            data.user_id is not None
            and await self.user_repository.get_by_id(data.user_id) is None
        ):
            raise ResourceNotFoundError("User not found")
        return await self.repository.create(data)


@dataclass(slots=True)
class UpdateTeamMember:
    repository: TeamMemberRepository
    user_repository: UserRepository

    async def execute(
        self, team_member_id: uuid.UUID, data: TeamMemberInput
    ) -> TeamMember:
        if (
            data.user_id is not None
            and await self.user_repository.get_by_id(data.user_id) is None
        ):
            raise ResourceNotFoundError("User not found")

        result = await self.repository.update(team_member_id, data)
        if result is None:
            raise ResourceNotFoundError("Team member not found")
        return result


@dataclass(slots=True)
class DeleteTeamMember:
    repository: TeamMemberRepository

    async def execute(self, team_member_id: uuid.UUID) -> None:
        deleted = await self.repository.delete(team_member_id)
        if not deleted:
            raise ResourceNotFoundError("Team member not found")
