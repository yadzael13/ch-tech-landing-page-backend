"""Partner entity (DATA_MODEL.md) — a technology or business alliance."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects import Image, Url


@dataclass(slots=True)
class Partner:
    id: uuid.UUID
    name: str
    logo: Image | None
    partnership_type: str | None
    website_url: Url | None
    created_at: datetime
    updated_at: datetime
