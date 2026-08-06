"""Company entity (DATA_MODEL.md).

Singleton: exactly one instance exists in the system. Enforced at the
application layer, not by this dataclass itself.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.value_objects import Email


@dataclass(slots=True)
class Company:
    id: uuid.UUID
    legal_name: str
    display_name: str
    tagline: str | None
    mission: str | None
    vision: str | None
    email: Email | None
    phone: str | None
    address: str | None
    social_links: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
