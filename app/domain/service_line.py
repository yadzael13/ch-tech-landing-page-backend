"""ServiceLine entity (DATA_MODEL.md) — one of CH-TECH's five business lines."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects import Image, Slug


@dataclass(slots=True)
class ServiceLine:
    id: uuid.UUID
    slug: Slug
    name: str
    description: str | None
    icon: Image | None
    display_order: int
    created_at: datetime
    updated_at: datetime
