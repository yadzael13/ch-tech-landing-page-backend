"""SQLAlchemy adapter for the TeamMemberRepository port (ADR-0012, Fase 6)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.team_member_repository import TeamMemberInput
from app.domain.team_member import TeamMember as TeamMemberEntity
from app.domain.value_objects import Image, Url
from app.models import TeamMember as TeamMemberModel


def _to_entity(model: TeamMemberModel) -> TeamMemberEntity:
    return TeamMemberEntity(
        id=model.id,
        user_id=model.user_id,
        name=model.name,
        role=model.role,
        bio=model.bio,
        photo=Image(model.photo) if model.photo else None,
        linkedin_url=Url(model.linkedin_url) if model.linkedin_url else None,
        github_url=Url(model.github_url) if model.github_url else None,
        display_order=model.display_order,
        active=model.active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyTeamMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, *, active_only: bool) -> list[TeamMemberEntity]:
        query = select(TeamMemberModel)
        if active_only:
            query = query.where(TeamMemberModel.active.is_(True))
        query = query.order_by(TeamMemberModel.display_order)

        result = await self._session.execute(query)
        return [_to_entity(model) for model in result.scalars().all()]

    async def get_by_id(
        self, team_member_id: uuid.UUID, *, active_only: bool
    ) -> TeamMemberEntity | None:
        query = select(TeamMemberModel).where(TeamMemberModel.id == team_member_id)
        if active_only:
            query = query.where(TeamMemberModel.active.is_(True))

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def create(self, data: TeamMemberInput) -> TeamMemberEntity:
        model = TeamMemberModel(
            user_id=data.user_id,
            name=data.name,
            role=data.role,
            bio=data.bio,
            photo=data.photo,
            linkedin_url=data.linkedin_url,
            github_url=data.github_url,
            display_order=data.display_order,
            active=data.active,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(
        self, team_member_id: uuid.UUID, data: TeamMemberInput
    ) -> TeamMemberEntity | None:
        result = await self._session.execute(
            select(TeamMemberModel).where(TeamMemberModel.id == team_member_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        model.user_id = data.user_id
        model.name = data.name
        model.role = data.role
        model.bio = data.bio
        model.photo = data.photo
        model.linkedin_url = data.linkedin_url
        model.github_url = data.github_url
        model.display_order = data.display_order
        model.active = data.active

        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, team_member_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(TeamMemberModel).where(TeamMemberModel.id == team_member_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.commit()
        return True
