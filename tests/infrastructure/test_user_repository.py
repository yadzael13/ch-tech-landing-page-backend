import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.models import User as UserModel


async def _make_user(
    db_session: AsyncSession, *, email: str | None = None
) -> UserModel:
    user = UserModel(
        name="Yadzael",
        email=email or f"{uuid.uuid4()}@ch-tech.dev",
        password_hash=hash_password("s3cret-pass"),
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyUserRepository(db_session)
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_get_by_id_returns_the_matching_user(db_session: AsyncSession) -> None:
    model = await _make_user(db_session)
    repo = SQLAlchemyUserRepository(db_session)

    result = await repo.get_by_id(model.id)

    assert result is not None
    assert str(result.email) == model.email


async def test_get_by_email_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyUserRepository(db_session)
    assert await repo.get_by_email("missing@ch-tech.dev") is None


async def test_get_by_email_returns_the_matching_user(db_session: AsyncSession) -> None:
    model = await _make_user(db_session, email="yadzael@ch-tech.dev")
    repo = SQLAlchemyUserRepository(db_session)

    result = await repo.get_by_email("yadzael@ch-tech.dev")

    assert result is not None
    assert result.id == model.id


async def test_record_login_sets_last_login(db_session: AsyncSession) -> None:
    model = await _make_user(db_session)
    await db_session.commit()
    repo = SQLAlchemyUserRepository(db_session)
    assert (await repo.get_by_id(model.id)).last_login is None  # type: ignore[union-attr]

    await repo.record_login(model.id, at=datetime.now(UTC))

    result = await repo.get_by_id(model.id)
    assert result is not None
    assert result.last_login is not None
