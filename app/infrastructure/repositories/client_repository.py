"""SQLAlchemy adapter for the ClientRepository port (ADR-0012, Fase 6)."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.client_repository import ClientInput
from app.core.errors import ConflictError
from app.domain.client import Client as ClientEntity
from app.domain.value_objects import Image, Url
from app.models import Client as ClientModel


def _to_entity(model: ClientModel) -> ClientEntity:
    return ClientEntity(
        id=model.id,
        name=model.name,
        logo=Image(model.logo) if model.logo else None,
        industry=model.industry,
        website_url=Url(model.website_url) if model.website_url else None,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[ClientEntity]:
        result = await self._session.execute(
            select(ClientModel).order_by(ClientModel.name)
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def get_by_id(self, client_id: uuid.UUID) -> ClientEntity | None:
        result = await self._session.execute(
            select(ClientModel).where(ClientModel.id == client_id)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def create(self, data: ClientInput) -> ClientEntity:
        model = ClientModel(
            name=data.name,
            logo=data.logo,
            industry=data.industry,
            website_url=data.website_url,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(
        self, client_id: uuid.UUID, data: ClientInput
    ) -> ClientEntity | None:
        result = await self._session.execute(
            select(ClientModel).where(ClientModel.id == client_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        model.name = data.name
        model.logo = data.logo
        model.industry = data.industry
        model.website_url = data.website_url

        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, client_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(ClientModel).where(ClientModel.id == client_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            raise ConflictError(
                "Client is referenced by an existing project or testimonial"
            ) from exc
        return True
