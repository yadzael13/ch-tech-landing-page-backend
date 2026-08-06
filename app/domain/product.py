"""Product entity (DATA_MODEL.md, ADR-0013) — a CH-TECH SaaS catalog entry.

Catalog only: no tenants, plans, or billing (ADR-0013).
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import ProductStatus
from app.domain.value_objects import Image, Slug, Url


@dataclass(slots=True)
class Product:
    id: uuid.UUID
    slug: Slug
    name: str
    short_description: str | None
    full_description: str | None
    status: ProductStatus
    url: Url | None
    logo: Image | None
    featured: bool
    created_at: datetime
    updated_at: datetime
