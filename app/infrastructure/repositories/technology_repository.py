"""SQLAlchemy adapter for the TechnologyRepository port (ADR-0012, Fase 4)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.technology_repository import (
    TechnologyFilters,
    TechnologyInput,
)
from app.domain.technology import Technology as TechnologyEntity
from app.domain.value_objects import Image, Url
from app.models import Technology as TechnologyModel


def _to_entity(model: TechnologyModel) -> TechnologyEntity:
    return TechnologyEntity(
        id=model.id,
        name=model.name,
        category=model.category,
        icon=Image(model.icon) if model.icon else None,
        official_url=Url(model.official_url) if model.official_url else None,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyTechnologyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, filters: TechnologyFilters) -> list[TechnologyEntity]:
        query = select(TechnologyModel)
        if filters.category is not None:
            query = query.where(TechnologyModel.category == filters.category)
        query = query.order_by(TechnologyModel.name)

        result = await self._session.execute(query)
        return [_to_entity(model) for model in result.scalars().all()]

    async def get_by_id(self, technology_id: uuid.UUID) -> TechnologyEntity | None:
        result = await self._session.execute(
            select(TechnologyModel).where(TechnologyModel.id == technology_id)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def create(self, data: TechnologyInput) -> TechnologyEntity:
        model = TechnologyModel(
            name=data.name,
            category=data.category,
            icon=data.icon,
            official_url=data.official_url,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(
        self, technology_id: uuid.UUID, data: TechnologyInput
    ) -> TechnologyEntity | None:
        result = await self._session.execute(
            select(TechnologyModel).where(TechnologyModel.id == technology_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        model.name = data.name
        model.category = data.category
        model.icon = data.icon
        model.official_url = data.official_url

        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, technology_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(TechnologyModel).where(TechnologyModel.id == technology_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.commit()
        return True
