import uuid
from datetime import UTC, datetime, timedelta

from app.domain.refresh_token import RefreshToken


def _token(**overrides: object) -> RefreshToken:
    issued_at = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "token_hash": "sha256-hash",
        "issued_at": issued_at,
        "expires_at": issued_at + timedelta(days=7),
        "revoked_at": None,
        "user_agent": None,
        "ip_address": None,
    }
    defaults.update(overrides)
    return RefreshToken(**defaults)  # type: ignore[arg-type]


def test_a_fresh_token_is_active() -> None:
    token = _token()
    assert token.is_active(at=token.issued_at) is True


def test_an_expired_token_is_not_active() -> None:
    token = _token()
    assert token.is_active(at=token.expires_at) is False


def test_a_revoked_token_is_not_active_even_if_unexpired() -> None:
    token = _token()
    token.revoke(at=token.issued_at + timedelta(hours=1))
    assert token.is_active(at=token.issued_at + timedelta(hours=2)) is False


def test_revoke_sets_revoked_at() -> None:
    token = _token()
    revoke_time = token.issued_at + timedelta(hours=1)
    token.revoke(at=revoke_time)
    assert token.revoked_at == revoke_time


def test_revoke_is_idempotent() -> None:
    token = _token()
    first_revoke = token.issued_at + timedelta(hours=1)
    second_revoke = token.issued_at + timedelta(hours=2)
    token.revoke(at=first_revoke)
    token.revoke(at=second_revoke)
    assert token.revoked_at == first_revoke
