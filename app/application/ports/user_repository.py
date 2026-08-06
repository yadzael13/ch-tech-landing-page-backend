"""UserRepository port (ADR-0012, ARCHITECTURE.md, Fase 4)."""

import uuid
from datetime import datetime
from typing import Protocol

from app.domain.user import User


class UserRepository(Protocol):
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def record_login(self, user_id: uuid.UUID, *, at: datetime) -> None: ...
