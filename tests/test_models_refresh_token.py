import uuid
from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import utcnow
from app.models.refresh_token import RefreshToken
from app.models.user import User


async def _create_user(db_session: AsyncSession) -> User:
    user = User(name="Yadzael", email="yadzael@ch-tech.dev", password_hash="hashed")
    db_session.add(user)
    await db_session.flush()
    return user


async def test_refresh_token_belongs_to_a_user(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    token = RefreshToken(
        user_id=user.id,
        token_hash="hash-1",
        issued_at=utcnow(),
        expires_at=utcnow() + timedelta(days=7),
    )
    db_session.add(token)
    await db_session.commit()

    assert token.user_id == user.id
    assert token.revoked_at is None


async def test_refresh_token_hash_must_be_unique(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    db_session.add(
        RefreshToken(
            user_id=user.id,
            token_hash="dup-hash",
            issued_at=utcnow(),
            expires_at=utcnow() + timedelta(days=7),
        )
    )
    await db_session.commit()

    db_session.add(
        RefreshToken(
            user_id=user.id,
            token_hash="dup-hash",
            issued_at=utcnow(),
            expires_at=utcnow() + timedelta(days=7),
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_refresh_token_requires_an_existing_user(
    db_session: AsyncSession,
) -> None:
    db_session.add(
        RefreshToken(
            user_id=uuid.uuid4(),
            token_hash="orphan-hash",
            issued_at=utcnow(),
            expires_at=utcnow() + timedelta(days=7),
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_refresh_token_can_be_queried_by_hash(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    db_session.add(
        RefreshToken(
            user_id=user.id,
            token_hash="findable-hash",
            issued_at=utcnow(),
            expires_at=utcnow() + timedelta(days=7),
        )
    )
    await db_session.commit()

    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == "findable-hash")
    )
    found = result.scalar_one()

    assert found.user_id == user.id
