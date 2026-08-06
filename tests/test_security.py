import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_hash_password_round_trip() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_verify_password_rejects_oversized_input_instead_of_raising() -> None:
    # bcrypt raises ValueError past 72 bytes instead of truncating; this must
    # be reported as "doesn't match" rather than propagate — an unhandled
    # 500 here (vs. a 401 for a merely-wrong password) is what turns into an
    # email-enumeration oracle at the /auth/login endpoint.
    password_hash = hash_password("short")

    assert not verify_password("a" * 100, password_hash)


def test_create_and_decode_access_token_round_trip() -> None:
    token = create_access_token(subject="user-id-123", role="ADMIN")

    payload = decode_access_token(token)

    assert payload["sub"] == "user-id-123"
    assert payload["role"] == "ADMIN"


def test_decode_access_token_rejects_tampered_token() -> None:
    token = create_access_token(subject="user-id-123", role="ADMIN")

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token + "tampered")


def test_generate_refresh_token_is_unique_each_time() -> None:
    assert generate_refresh_token() != generate_refresh_token()


def test_hash_refresh_token_is_deterministic() -> None:
    raw = generate_refresh_token()

    assert hash_refresh_token(raw) == hash_refresh_token(raw)
    assert hash_refresh_token(raw) != hash_refresh_token(generate_refresh_token())
