import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def test_user_defaults(db_session: AsyncSession) -> None:
    user = User(name="Yadzael", email="yadzael@ch-tech.dev", password_hash="hashed")
    db_session.add(user)
    await db_session.commit()

    assert user.role == UserRole.ADMIN.value
    assert user.is_active is True
    assert user.last_login is None
    assert user.created_at is not None
    assert user.updated_at is not None


async def test_user_email_must_be_unique(db_session: AsyncSession) -> None:
    db_session.add(User(name="A", email="dup@ch-tech.dev", password_hash="hashed"))
    await db_session.commit()

    db_session.add(User(name="B", email="dup@ch-tech.dev", password_hash="hashed"))
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_user_email_unique_index_is_case_insensitive(
    db_session: AsyncSession,
) -> None:
    # Defense in depth for the Email value object's normalization (see
    # domain/value_objects.py): backstops any write path that bypasses it —
    # this inserts raw model instances, the same as that path would.
    db_session.add(User(name="A", email="dup@ch-tech.dev", password_hash="hashed"))
    await db_session.commit()

    db_session.add(User(name="B", email="Dup@CH-TECH.dev", password_hash="hashed"))
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_user_role_check_constraint_rejects_invalid_role(
    db_session: AsyncSession,
) -> None:
    db_session.add(
        User(
            name="Bad",
            email="bad@ch-tech.dev",
            password_hash="hashed",
            role="NOT_A_ROLE",
        )
    )
    # MySQL raises CHECK constraint violations as OperationalError (error
    # 3819), not IntegrityError like Postgres — unlike UNIQUE/FK violations
    # above, which both dialects agree map to IntegrityError.
    with pytest.raises(OperationalError):
        await db_session.commit()


async def test_user_can_be_queried_by_email(db_session: AsyncSession) -> None:
    db_session.add(User(name="Q", email="query@ch-tech.dev", password_hash="hashed"))
    await db_session.commit()

    result = await db_session.execute(
        select(User).where(User.email == "query@ch-tech.dev")
    )
    found = result.scalar_one()

    assert found.name == "Q"
