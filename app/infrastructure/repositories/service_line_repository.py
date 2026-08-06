"""SQLAlchemy adapter for the ServiceLineRepository port (ADR-0012, Fase 6)."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.service_line_repository import ServiceLineInput
from app.core.errors import ConflictError
from app.domain.service_line import ServiceLine as ServiceLineEntity
from app.domain.value_objects import Image, Slug
from app.models import ServiceLine as ServiceLineModel


def _to_entity(model: ServiceLineModel) -> ServiceLineEntity:
    return ServiceLineEntity(
        id=model.id,
        slug=Slug(model.slug),
        name=model.name,
        description=model.description,
        icon=Image(model.icon) if model.icon else None,
        display_order=model.display_order,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyServiceLineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[ServiceLineEntity]:
        result = await self._session.execute(
            select(ServiceLineModel).order_by(ServiceLineModel.display_order)
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def get_by_slug(self, slug: str) -> ServiceLineEntity | None:
        result = await self._session.execute(
            select(ServiceLineModel).where(ServiceLineModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def create(self, data: ServiceLineInput) -> ServiceLineEntity:
        model = ServiceLineModel(
            slug=data.slug,
            name=data.name,
            description=data.description,
            icon=data.icon,
            display_order=data.display_order,
        )
        self._session.add(model)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            raise ConflictError("A service line with this slug already exists") from exc

        await self._session.refresh(model)
        return _to_entity(model)

    async def update(
        self, service_line_id: uuid.UUID, data: ServiceLineInput
    ) -> ServiceLineEntity | None:
        result = await self._session.execute(
            select(ServiceLineModel).where(ServiceLineModel.id == service_line_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        model.slug = data.slug
        model.name = data.name
        model.description = data.description
        model.icon = data.icon
        model.display_order = data.display_order

        try:
            await self._session.commit()
        except IntegrityError as exc:
            raise ConflictError("A service line with this slug already exists") from exc

        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, service_line_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(ServiceLineModel).where(ServiceLineModel.id == service_line_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            raise ConflictError(
                "Service line is referenced by an existing service or contact request"
            ) from exc
        return True
