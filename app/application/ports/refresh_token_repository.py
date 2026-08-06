"""RefreshTokenRepository port (ADR-0012, ARCHITECTURE.md, Fase 4)."""

import uuid
from datetime import datetime
from typing import Protocol

from app.domain.refresh_token import RefreshToken


class RefreshTokenRepository(Protocol):
    async def create(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        issued_at: datetime,
        expires_at: datetime,
        user_agent: str | None,
        ip_address: str | None,
    ) -> RefreshToken: ...

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None: ...

    async def save(self, token: RefreshToken) -> None:
        """Persist mutations made via the entity's own revoke()."""
        ...

    async def revoke_if_active(
        self, token_hash: str, *, at: datetime
    ) -> RefreshToken | None:
        """Atomically revoke the token iff it was active at `at`, in one
        conditional write — read-then-write would let two concurrent callers
        both observe "active" before either commits the revocation,
        defeating single-use rotation. Returns None for "doesn't exist",
        "already revoked", and "expired" alike, matching the caller's
        uniform error for all three.
        """
        ...

    async def purge_older_than(self, cutoff: datetime) -> int:
        """Delete tokens that expired, or were revoked, before `cutoff`.

        Returns the number of rows deleted. Nothing else in this repository
        ever removes a row — without this, refresh_tokens grows without
        bound (DATABASE_SCHEMA.md "refresh_tokens").
        """
        ...
