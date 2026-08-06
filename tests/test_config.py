import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_reads_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host/db")

    settings = Settings()

    assert settings.database_url == "postgresql+asyncpg://u:p@host/db"


def test_settings_rejects_a_jwt_secret_key_shorter_than_32_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "too-short")

    with pytest.raises(ValidationError):
        Settings()
