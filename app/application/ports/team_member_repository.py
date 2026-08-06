"""TeamMemberRepository port (ADR-0012, ARCHITECTURE.md, Fase 6)."""

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.domain.team_member import TeamMember


@dataclass(slots=True)
class TeamMemberInput:
    user_id: uuid.UUID | None
    name: str
    role: str
    bio: str | None
    photo: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    display_order: int = 0
    active: bool = True


class TeamMemberRepository(Protocol):
    async def list(self, *, active_only: bool) -> list[TeamMember]: ...

    async def get_by_id(
        self, team_member_id: uuid.UUID, *, active_only: bool
    ) -> TeamMember | None: ...

    async def create(self, data: TeamMemberInput) -> TeamMember: ...

    async def update(
        self, team_member_id: uuid.UUID, data: TeamMemberInput
    ) -> TeamMember | None: ...

    async def delete(self, team_member_id: uuid.UUID) -> bool: ...
