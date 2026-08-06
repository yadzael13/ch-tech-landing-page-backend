import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.application.use_cases.auth import (
    Login,
    Logout,
    PurgeExpiredRefreshTokens,
    RefreshAccessToken,
)
from app.core.errors import UnauthorizedError
from app.core.security import hash_password, hash_refresh_token
from app.domain.enums import UserRole
from app.domain.refresh_token import RefreshToken
from app.domain.user import User
from app.domain.value_objects import Email
from tests.application.fakes import (
    InMemoryRefreshTokenRepository,
    InMemoryUserRepository,
)


def _user(**overrides: object) -> User:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "name": "Yadzael",
        "email": Email("yadzael@ch-tech.dev"),
        "password_hash": hash_password("s3cret-pass"),
        "role": UserRole.ADMIN,
        "is_active": True,
        "last_login": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return User(**defaults)  # type: ignore[arg-type]


def _token(**overrides: object) -> RefreshToken:
    # RefreshAccessToken.execute() checks is_active() against the real
    # datetime.now(UTC), not a fixed instant — anchor defaults there too,
    # unlike the pure domain tests in tests/domain/test_refresh_token.py
    # which pass an explicit `at` and can use any fixed anchor.
    issued_at = datetime.now(UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "token_hash": hash_refresh_token("raw-token"),
        "issued_at": issued_at,
        "expires_at": issued_at + timedelta(days=7),
        "revoked_at": None,
        "user_agent": None,
        "ip_address": None,
    }
    defaults.update(overrides)
    return RefreshToken(**defaults)  # type: ignore[arg-type]


async def test_login_rejects_an_unknown_email() -> None:
    use_case = Login(
        user_repository=InMemoryUserRepository(),
        refresh_token_repository=InMemoryRefreshTokenRepository(),
        refresh_token_ttl=timedelta(days=7),
    )

    with pytest.raises(UnauthorizedError):
        await use_case.execute(
            email="missing@ch-tech.dev",
            password="whatever",
            user_agent=None,
            ip_address=None,
        )


async def test_login_rejects_a_wrong_password() -> None:
    user = _user()
    use_case = Login(
        user_repository=InMemoryUserRepository([user]),
        refresh_token_repository=InMemoryRefreshTokenRepository(),
        refresh_token_ttl=timedelta(days=7),
    )

    with pytest.raises(UnauthorizedError):
        await use_case.execute(
            email=str(user.email), password="wrong", user_agent=None, ip_address=None
        )


async def test_login_with_valid_credentials_returns_tokens_and_persists_one() -> None:
    user = _user()
    refresh_repo = InMemoryRefreshTokenRepository()
    use_case = Login(
        user_repository=InMemoryUserRepository([user]),
        refresh_token_repository=refresh_repo,
        refresh_token_ttl=timedelta(days=7),
    )

    result = await use_case.execute(
        email=str(user.email),
        password="s3cret-pass",
        user_agent="pytest",
        ip_address="127.0.0.1",
    )

    assert result.access_token
    assert result.refresh_token
    stored = await refresh_repo.get_by_token_hash(
        hash_refresh_token(result.refresh_token)
    )
    assert stored is not None
    assert stored.user_id == user.id


async def test_login_records_last_login_on_success() -> None:
    user = _user()
    user_repo = InMemoryUserRepository([user])
    use_case = Login(
        user_repository=user_repo,
        refresh_token_repository=InMemoryRefreshTokenRepository(),
        refresh_token_ttl=timedelta(days=7),
    )

    await use_case.execute(
        email=str(user.email), password="s3cret-pass", user_agent=None, ip_address=None
    )

    updated = await user_repo.get_by_id(user.id)
    assert updated is not None
    assert updated.last_login is not None


async def test_login_rejects_a_deactivated_user() -> None:
    user = _user(is_active=False)
    use_case = Login(
        user_repository=InMemoryUserRepository([user]),
        refresh_token_repository=InMemoryRefreshTokenRepository(),
        refresh_token_ttl=timedelta(days=7),
    )

    with pytest.raises(UnauthorizedError):
        await use_case.execute(
            email=str(user.email),
            password="s3cret-pass",
            user_agent=None,
            ip_address=None,
        )


async def test_logout_rejects_an_unknown_token() -> None:
    use_case = Logout(refresh_token_repository=InMemoryRefreshTokenRepository())

    with pytest.raises(UnauthorizedError):
        await use_case.execute(
            raw_refresh_token="does-not-exist", current_user_id=uuid.uuid4()
        )


async def test_logout_rejects_a_token_owned_by_someone_else() -> None:
    owner_id = uuid.uuid4()
    token = _token(user_id=owner_id, token_hash=hash_refresh_token("owners-token"))
    use_case = Logout(refresh_token_repository=InMemoryRefreshTokenRepository([token]))

    with pytest.raises(UnauthorizedError):
        await use_case.execute(
            raw_refresh_token="owners-token", current_user_id=uuid.uuid4()
        )


async def test_logout_revokes_the_token() -> None:
    owner_id = uuid.uuid4()
    token = _token(user_id=owner_id, token_hash=hash_refresh_token("my-token"))
    repo = InMemoryRefreshTokenRepository([token])
    use_case = Logout(refresh_token_repository=repo)

    await use_case.execute(raw_refresh_token="my-token", current_user_id=owner_id)

    saved = await repo.get_by_token_hash(hash_refresh_token("my-token"))
    assert saved is not None
    assert saved.revoked_at is not None


async def test_refresh_rejects_an_unknown_token() -> None:
    use_case = RefreshAccessToken(
        user_repository=InMemoryUserRepository(),
        refresh_token_repository=InMemoryRefreshTokenRepository(),
        refresh_token_ttl=timedelta(days=7),
    )

    with pytest.raises(UnauthorizedError):
        await use_case.execute(
            raw_refresh_token="does-not-exist", user_agent=None, ip_address=None
        )


async def test_refresh_rejects_an_expired_token() -> None:
    user = _user()
    token = _token(
        user_id=user.id,
        token_hash=hash_refresh_token("expired-token"),
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    use_case = RefreshAccessToken(
        user_repository=InMemoryUserRepository([user]),
        refresh_token_repository=InMemoryRefreshTokenRepository([token]),
        refresh_token_ttl=timedelta(days=7),
    )

    with pytest.raises(UnauthorizedError):
        await use_case.execute(
            raw_refresh_token="expired-token", user_agent=None, ip_address=None
        )


async def test_refresh_rejects_an_already_revoked_token() -> None:
    user = _user()
    token = _token(
        user_id=user.id,
        token_hash=hash_refresh_token("revoked-token"),
        revoked_at=datetime.now(UTC),
    )
    use_case = RefreshAccessToken(
        user_repository=InMemoryUserRepository([user]),
        refresh_token_repository=InMemoryRefreshTokenRepository([token]),
        refresh_token_ttl=timedelta(days=7),
    )

    with pytest.raises(UnauthorizedError):
        await use_case.execute(
            raw_refresh_token="revoked-token", user_agent=None, ip_address=None
        )


async def test_refresh_rotates_and_returns_new_tokens() -> None:
    user = _user()
    token = _token(user_id=user.id, token_hash=hash_refresh_token("old-token"))
    refresh_repo = InMemoryRefreshTokenRepository([token])
    use_case = RefreshAccessToken(
        user_repository=InMemoryUserRepository([user]),
        refresh_token_repository=refresh_repo,
        refresh_token_ttl=timedelta(days=7),
    )

    result = await use_case.execute(
        raw_refresh_token="old-token", user_agent=None, ip_address=None
    )

    assert result.access_token
    assert result.refresh_token != "old-token"

    old = await refresh_repo.get_by_token_hash(hash_refresh_token("old-token"))
    assert old is not None
    assert old.revoked_at is not None

    new = await refresh_repo.get_by_token_hash(hash_refresh_token(result.refresh_token))
    assert new is not None
    assert new.user_id == user.id


async def test_refresh_rejects_a_deactivated_user() -> None:
    user = _user(is_active=False)
    token = _token(user_id=user.id, token_hash=hash_refresh_token("deactivated-token"))
    use_case = RefreshAccessToken(
        user_repository=InMemoryUserRepository([user]),
        refresh_token_repository=InMemoryRefreshTokenRepository([token]),
        refresh_token_ttl=timedelta(days=7),
    )

    with pytest.raises(UnauthorizedError):
        await use_case.execute(
            raw_refresh_token="deactivated-token", user_agent=None, ip_address=None
        )


async def test_refresh_rejects_a_second_use_of_the_same_token() -> None:
    user = _user()
    token = _token(user_id=user.id, token_hash=hash_refresh_token("reused-token"))
    use_case = RefreshAccessToken(
        user_repository=InMemoryUserRepository([user]),
        refresh_token_repository=InMemoryRefreshTokenRepository([token]),
        refresh_token_ttl=timedelta(days=7),
    )

    await use_case.execute(
        raw_refresh_token="reused-token", user_agent=None, ip_address=None
    )

    with pytest.raises(UnauthorizedError):
        await use_case.execute(
            raw_refresh_token="reused-token", user_agent=None, ip_address=None
        )


async def test_purge_expired_refresh_tokens_deletes_past_retention() -> None:
    old_token = _token(
        token_hash=hash_refresh_token("old"),
        expires_at=datetime.now(UTC) - timedelta(days=40),
    )
    fresh_token = _token(
        token_hash=hash_refresh_token("fresh"),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    repo = InMemoryRefreshTokenRepository([old_token, fresh_token])
    use_case = PurgeExpiredRefreshTokens(
        refresh_token_repository=repo, retention=timedelta(days=30)
    )

    deleted = await use_case.execute()

    assert deleted == 1
    assert await repo.get_by_token_hash(hash_refresh_token("old")) is None
    assert await repo.get_by_token_hash(hash_refresh_token("fresh")) is not None
