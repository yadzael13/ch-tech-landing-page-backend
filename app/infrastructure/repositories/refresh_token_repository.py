"""SQLAlchemy adapter for the RefreshTokenRepository port (ADR-0012, Fase 4)."""

import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.refresh_token import RefreshToken as RefreshTokenEntity
from app.models import RefreshToken as RefreshTokenModel


def _to_entity(model: RefreshTokenModel) -> RefreshTokenEntity:
    return RefreshTokenEntity(
        id=model.id,
        user_id=model.user_id,
        token_hash=model.token_hash,
        issued_at=model.issued_at,
        expires_at=model.expires_at,
        revoked_at=model.revoked_at,
        user_agent=model.user_agent,
        ip_address=model.ip_address,
    )


class SQLAlchemyRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        issued_at: datetime,
        expires_at: datetime,
        user_agent: str | None,
        ip_address: str | None,
    ) -> RefreshTokenEntity:
        model = RefreshTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            issued_at=issued_at,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def get_by_token_hash(self, token_hash: str) -> RefreshTokenEntity | None:
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def save(self, token: RefreshTokenEntity) -> None:
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.id == token.id)
        )
        model = result.scalar_one()
        model.revoked_at = token.revoked_at
        await self._session.commit()

    async def revoke_if_active(
        self, token_hash: str, *, at: datetime
    ) -> RefreshTokenEntity | None:
        # MySQL has no RETURNING (unlike the Postgres UPDATE...RETURNING this
        # replaces) — SELECT ... FOR UPDATE locks the row first so a
        # concurrent double-refresh can't both read "active" before either
        # commits, then the ORM mutation + commit does the update.
        result = await self._session.execute(
            select(RefreshTokenModel)
            .where(
                RefreshTokenModel.token_hash == token_hash,
                RefreshTokenModel.revoked_at.is_(None),
                RefreshTokenModel.expires_at > at,
            )
            .with_for_update()
        )
        model = result.scalar_one_or_none()
        if model is None:
            await self._session.commit()
            return None
        model.revoked_at = at
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def purge_older_than(self, cutoff: datetime) -> int:
        # MySQL has no RETURNING — SELECT the matching ids first, then
        # DELETE by id. This is a daily offline cron job
        # (app/db/purge_refresh_tokens.py), not a concurrency-sensitive
        # request path, so the two-step isn't a race concern.
        where_clause = (RefreshTokenModel.expires_at < cutoff) | (
            RefreshTokenModel.revoked_at.is_not(None)
            & (RefreshTokenModel.revoked_at < cutoff)
        )
        result = await self._session.execute(
            select(RefreshTokenModel.id).where(where_clause)
        )
        ids = list(result.scalars().all())
        if not ids:
            return 0
        await self._session.execute(
            delete(RefreshTokenModel).where(RefreshTokenModel.id.in_(ids))
        )
        await self._session.commit()
        return len(ids)
