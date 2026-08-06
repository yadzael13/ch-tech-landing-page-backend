"""Client entity (DATA_MODEL.md) — a company CH-TECH has worked with."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects import Image, Url


@dataclass(slots=True)
class Client:
    id: uuid.UUID
    name: str
    logo: Image | None
    industry: str | None
    website_url: Url | None
    created_at: datetime
    updated_at: datetime
