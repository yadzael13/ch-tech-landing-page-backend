"""Service entity (DATA_MODEL.md).

service_line_id is documented as required once CH-TECH V2's ServiceLine
table exists (Fase 5), but that migration hasn't landed yet — the services
table has no such column today. Kept optional here so this entity can be
constructed from the current schema; Fase 5 tightens it to non-null.

created_at/updated_at were missing from this entity in Fase 2 despite
DATA_MODEL.md listing them — fixed here in Fase 4 when ServiceItem
(API.md) needed them, same gap as app.domain.technology.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects import Slug


@dataclass(slots=True)
class Service:
    id: uuid.UUID
    service_line_id: uuid.UUID | None
    title: str
    slug: Slug
    description: str | None
    featured: bool
    active: bool
    created_at: datetime
    updated_at: datetime
