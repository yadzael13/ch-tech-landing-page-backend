"""Auth use cases (ADR-0012, Fase 4).

Password hashing/verification and JWT creation (app.core.security) are
framework-agnostic pure functions — no FastAPI/SQLAlchemy dependency — so
the application layer calls them directly rather than hiding them behind
another port (ARCHITECTURE.md treats app.core as a shared kernel, same
reasoning already applied to app.core.errors in the projects/articles
use cases).
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.application.ports.refresh_token_repository import RefreshTokenRepository
from app.application.ports.user_repository import UserRepository
from app.core.errors import UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)


@dataclass(slots=True)
class AuthTokens:
    access_token: str
    refresh_token: str


async def _issue_refresh_token(
    repository: RefreshTokenRepository,
    *,
    user_id: uuid.UUID,
    ttl: timedelta,
    user_agent: str | None,
    ip_address: str | None,
) -> str:
    raw_token = generate_refresh_token()
    now = datetime.now(UTC)
    await repository.create(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        issued_at=now,
        expires_at=now + ttl,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    return raw_token


@dataclass(slots=True)
class Login:
    user_repository: UserRepository
    refresh_token_repository: RefreshTokenRepository
    refresh_token_ttl: timedelta

    async def execute(
        self,
        *,
        email: str,
        password: str,
        user_agent: str | None,
        ip_address: str | None,
    ) -> AuthTokens:
        # Normalize the same way the stored value is (Email value object,
        # domain/value_objects.py): otherwise a case-sensitive `==` lookup
        # against a lowercase-stored address rejects a correct email/password
        # pair just because of how the caller capitalized it.
        user = await self.user_repository.get_by_email(email.strip().lower())
        # Same error for "no such user", "wrong password", and "deactivated
        # account" — a different message for any of these would let an
        # attacker enumerate valid/active emails.
        if (
            user is None
            or not user.is_active
            or not verify_password(password, user.password_hash)
        ):
            raise UnauthorizedError("Invalid email or password")

        now = datetime.now(UTC)
        await self.user_repository.record_login(user.id, at=now)

        raw_refresh_token = await _issue_refresh_token(
            self.refresh_token_repository,
            user_id=user.id,
            ttl=self.refresh_token_ttl,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        access_token = create_access_token(subject=str(user.id), role=user.role.value)
        return AuthTokens(access_token=access_token, refresh_token=raw_refresh_token)


@dataclass(slots=True)
class Logout:
    refresh_token_repository: RefreshTokenRepository

    async def execute(
        self, *, raw_refresh_token: str, current_user_id: uuid.UUID
    ) -> None:
        token = await self.refresh_token_repository.get_by_token_hash(
            hash_refresh_token(raw_refresh_token)
        )
        # Same error whether the token doesn't exist or belongs to someone
        # else — doesn't tell a caller with a stolen access token which is
        # the case.
        if token is None or token.user_id != current_user_id:
            raise UnauthorizedError("Invalid refresh token")

        token.revoke(at=datetime.now(UTC))
        await self.refresh_token_repository.save(token)


@dataclass(slots=True)
class PurgeExpiredRefreshTokens:
    """Deletes refresh_tokens rows past their retention window (run
    periodically via app.db.purge_refresh_tokens, not from an HTTP route —
    the table has no other cleanup path, see DATABASE_SCHEMA.md)."""

    refresh_token_repository: RefreshTokenRepository
    retention: timedelta

    async def execute(self) -> int:
        cutoff = datetime.now(UTC) - self.retention
        return await self.refresh_token_repository.purge_older_than(cutoff)


@dataclass(slots=True)
class RefreshAccessToken:
    user_repository: UserRepository
    refresh_token_repository: RefreshTokenRepository
    refresh_token_ttl: timedelta

    async def execute(
        self,
        *,
        raw_refresh_token: str,
        user_agent: str | None,
        ip_address: str | None,
    ) -> AuthTokens:
        now = datetime.now(UTC)
        # Rotation: the presented token is single-use. revoke_if_active does
        # the "still active?" check and the revoke in one atomic write, so
        # two concurrent requests replaying the same token can't both read
        # it as active before either commits — only one can win the race.
        # Revoking (not deleting) keeps an audit trail of the session's
        # history.
        token = await self.refresh_token_repository.revoke_if_active(
            hash_refresh_token(raw_refresh_token), at=now
        )
        if token is None:
            raise UnauthorizedError("Invalid or expired refresh token")

        user = await self.user_repository.get_by_id(token.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Invalid or expired refresh token")

        raw_new_refresh_token = await _issue_refresh_token(
            self.refresh_token_repository,
            user_id=user.id,
            ttl=self.refresh_token_ttl,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        access_token = create_access_token(subject=str(user.id), role=user.role.value)
        return AuthTokens(
            access_token=access_token, refresh_token=raw_new_refresh_token
        )
