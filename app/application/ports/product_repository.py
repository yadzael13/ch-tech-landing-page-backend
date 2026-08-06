"""ProductRepository port (ADR-0012, ARCHITECTURE.md, Fase 6)."""

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.domain.enums import ProductStatus
from app.domain.product import Product


@dataclass(slots=True)
class ProductInput:
    slug: str
    name: str
    short_description: str | None
    full_description: str | None
    status: ProductStatus
    url: str | None = None
    logo: str | None = None
    featured: bool = False


class ProductRepository(Protocol):
    async def list(self) -> list[Product]: ...

    async def get_by_slug(self, slug: str) -> Product | None: ...

    async def create(self, data: ProductInput) -> Product: ...

    async def update(
        self, product_id: uuid.UUID, data: ProductInput
    ) -> Product | None: ...

    async def delete(self, product_id: uuid.UUID) -> bool: ...
