"""SQLAlchemy adapter for the UserRepository port (ADR-0012, Fase 4)."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import UserRole
from app.domain.user import User as UserEntity
from app.domain.value_objects import Email
from app.models import User as UserModel


def _to_entity(model: UserModel) -> UserEntity:
    return UserEntity(
        id=model.id,
        name=model.name,
        email=Email(model.email),
        password_hash=model.password_hash,
        role=UserRole(model.role),
        is_active=model.is_active,
        last_login=model.last_login,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> UserEntity | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_email(self, email: str) -> UserEntity | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def record_login(self, user_id: uuid.UUID, *, at: datetime) -> None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one()
        model.last_login = at
        await self._session.commit()
