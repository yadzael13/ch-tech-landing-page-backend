"""SQLAlchemy adapter for the PartnerRepository port (ADR-0012, Fase 6)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.partner_repository import PartnerInput
from app.domain.partner import Partner as PartnerEntity
from app.domain.value_objects import Image, Url
from app.models import Partner as PartnerModel


def _to_entity(model: PartnerModel) -> PartnerEntity:
    return PartnerEntity(
        id=model.id,
        name=model.name,
        logo=Image(model.logo) if model.logo else None,
        partnership_type=model.partnership_type,
        website_url=Url(model.website_url) if model.website_url else None,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyPartnerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[PartnerEntity]:
        result = await self._session.execute(
            select(PartnerModel).order_by(PartnerModel.name)
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def get_by_id(self, partner_id: uuid.UUID) -> PartnerEntity | None:
        result = await self._session.execute(
            select(PartnerModel).where(PartnerModel.id == partner_id)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def create(self, data: PartnerInput) -> PartnerEntity:
        model = PartnerModel(
            name=data.name,
            logo=data.logo,
            partnership_type=data.partnership_type,
            website_url=data.website_url,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(
        self, partner_id: uuid.UUID, data: PartnerInput
    ) -> PartnerEntity | None:
        result = await self._session.execute(
            select(PartnerModel).where(PartnerModel.id == partner_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        model.name = data.name
        model.logo = data.logo
        model.partnership_type = data.partnership_type
        model.website_url = data.website_url

        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, partner_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(PartnerModel).where(PartnerModel.id == partner_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.commit()
        return True
