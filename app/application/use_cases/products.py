"""Product use cases (ADR-0012, Fase 6)."""

import uuid
from dataclasses import dataclass

from app.application.ports.product_repository import ProductInput, ProductRepository
from app.core.errors import ResourceNotFoundError
from app.domain.product import Product


@dataclass(slots=True)
class ListProducts:
    repository: ProductRepository

    async def execute(self) -> list[Product]:
        return await self.repository.list()


@dataclass(slots=True)
class GetProductBySlug:
    repository: ProductRepository

    async def execute(self, slug: str) -> Product:
        result = await self.repository.get_by_slug(slug)
        if result is None:
            raise ResourceNotFoundError("Product not found")
        return result


@dataclass(slots=True)
class CreateProduct:
    repository: ProductRepository

    async def execute(self, data: ProductInput) -> Product:
        return await self.repository.create(data)


@dataclass(slots=True)
class UpdateProduct:
    repository: ProductRepository

    async def execute(self, product_id: uuid.UUID, data: ProductInput) -> Product:
        result = await self.repository.update(product_id, data)
        if result is None:
            raise ResourceNotFoundError("Product not found")
        return result


@dataclass(slots=True)
class DeleteProduct:
    repository: ProductRepository

    async def execute(self, product_id: uuid.UUID) -> None:
        deleted = await self.repository.delete(product_id)
        if not deleted:
            raise ResourceNotFoundError("Product not found")
