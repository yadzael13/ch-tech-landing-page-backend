"""SQLAlchemy adapter for the ProductRepository port (ADR-0012, Fase 6)."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.product_repository import ProductInput
from app.core.errors import ConflictError
from app.domain.enums import ProductStatus
from app.domain.product import Product as ProductEntity
from app.domain.value_objects import Image, Slug, Url
from app.models import Product as ProductModel


def _to_entity(model: ProductModel) -> ProductEntity:
    return ProductEntity(
        id=model.id,
        slug=Slug(model.slug),
        name=model.name,
        short_description=model.short_description,
        full_description=model.full_description,
        status=ProductStatus(model.status),
        url=Url(model.url) if model.url else None,
        logo=Image(model.logo) if model.logo else None,
        featured=model.featured,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[ProductEntity]:
        result = await self._session.execute(
            select(ProductModel).order_by(ProductModel.name)
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def get_by_slug(self, slug: str) -> ProductEntity | None:
        result = await self._session.execute(
            select(ProductModel).where(ProductModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def create(self, data: ProductInput) -> ProductEntity:
        model = ProductModel(
            slug=data.slug,
            name=data.name,
            short_description=data.short_description,
            full_description=data.full_description,
            status=data.status.value,
            url=data.url,
            logo=data.logo,
            featured=data.featured,
        )
        self._session.add(model)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            raise ConflictError("A product with this slug already exists") from exc

        await self._session.refresh(model)
        return _to_entity(model)

    async def update(
        self, product_id: uuid.UUID, data: ProductInput
    ) -> ProductEntity | None:
        result = await self._session.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        model.slug = data.slug
        model.name = data.name
        model.short_description = data.short_description
        model.full_description = data.full_description
        model.status = data.status.value
        model.url = data.url
        model.logo = data.logo
        model.featured = data.featured

        try:
            await self._session.commit()
        except IntegrityError as exc:
            raise ConflictError("A product with this slug already exists") from exc

        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, product_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.commit()
        return True
