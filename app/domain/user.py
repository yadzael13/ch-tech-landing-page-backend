"""User entity (DATA_MODEL.md — administrator of the system, ADR-0003)."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import UserRole
from app.domain.value_objects import Email


@dataclass(slots=True)
class User:
    id: uuid.UUID
    name: str
    email: Email
    password_hash: str
    role: UserRole
    is_active: bool
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime
