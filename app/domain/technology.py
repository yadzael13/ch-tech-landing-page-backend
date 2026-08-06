"""Technology entity (DATA_MODEL.md).

created_at/updated_at were missing from this entity in Fase 2 — DATA_MODEL.md's
own attribute list for Technology omitted them, even though DATABASE_SCHEMA.md
and the persisted model both carry audit columns like every other entity.
Fixed here in Fase 4 when TechnologyItem (API.md) needed them.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects import Image, Url


@dataclass(slots=True)
class Technology:
    id: uuid.UUID
    name: str
    category: str | None
    icon: Image | None
    official_url: Url | None
    created_at: datetime
    updated_at: datetime
