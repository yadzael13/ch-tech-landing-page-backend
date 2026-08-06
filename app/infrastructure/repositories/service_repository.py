"""SQLAlchemy adapter for the ServiceRepository port (ADR-0012, Fase 4)."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.service_repository import ServiceInput
from app.core.errors import ConflictError
from app.domain.service import Service as ServiceEntity
from app.domain.value_objects import Slug
from app.models import Service as ServiceModel


def _to_entity(model: ServiceModel) -> ServiceEntity:
    return ServiceEntity(
        id=model.id,
        service_line_id=model.service_line_id,
        title=model.title,
        slug=Slug(model.slug),
        description=model.description,
        featured=model.featured,
        active=model.active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyServiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, *, active_only: bool) -> list[ServiceEntity]:
        query = select(ServiceModel)
        if active_only:
            query = query.where(ServiceModel.active.is_(True))
        query = query.order_by(ServiceModel.title)

        result = await self._session.execute(query)
        return [_to_entity(model) for model in result.scalars().all()]

    async def get_by_slug(
        self, slug: str, *, active_only: bool
    ) -> ServiceEntity | None:
        query = select(ServiceModel).where(ServiceModel.slug == slug)
        if active_only:
            query = query.where(ServiceModel.active.is_(True))

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_id(self, service_id: uuid.UUID) -> ServiceEntity | None:
        result = await self._session.execute(
            select(ServiceModel).where(ServiceModel.id == service_id)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def create(self, data: ServiceInput) -> ServiceEntity:
        model = ServiceModel(
            slug=data.slug,
            title=data.title,
            description=data.description,
            featured=data.featured,
            active=data.active,
        )
        self._session.add(model)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            raise ConflictError("A service with this slug already exists") from exc

        await self._session.refresh(model)
        return _to_entity(model)

    async def update(
        self, service_id: uuid.UUID, data: ServiceInput
    ) -> ServiceEntity | None:
        result = await self._session.execute(
            select(ServiceModel).where(ServiceModel.id == service_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        model.slug = data.slug
        model.title = data.title
        model.description = data.description
        model.featured = data.featured
        model.active = data.active

        try:
            await self._session.commit()
        except IntegrityError as exc:
            raise ConflictError("A service with this slug already exists") from exc

        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, service_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(ServiceModel).where(ServiceModel.id == service_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.commit()
        return True
