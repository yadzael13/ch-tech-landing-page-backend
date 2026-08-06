from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DML-only credential (chtech_app): used by the running app. Must never
    # be granted CREATE/ALTER/DROP — see docs/adr/0001-mysql-database-
    # privilege-separation.md. This is the DB-enforced guarantee that no
    # code path (including a future AI feature) can alter table structure.
    database_url: str
    # DDL credential (chtech_migrator): used ONLY by Alembic (alembic/env.py)
    # and by the test suite's ephemeral database bootstrap. Never imported
    # by app runtime code.
    migration_database_url: str
    redis_url: str

    # Single origin: CH-TECH serves one frontend (ADR-0002 rules out
    # multi-tenant use), so a CSV/list setting would be unused flexibility.
    frontend_origin: str = "http://localhost:3000"

    # No default: an accidentally-shared signing secret is a real
    # vulnerability, unlike the seed placeholders below (SECURITY.md).
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    # How long a refresh_tokens row survives past expiry/revocation before
    # app.db.purge_refresh_tokens deletes it. Independent of
    # refresh_token_expire_days: this is retention of the dead row, not
    # validity of the token itself.
    refresh_token_retention_days: int = 30

    @field_validator("jwt_secret_key")
    @classmethod
    def _validate_jwt_secret_strength(cls, value: str) -> str:
        # RFC 7518 3.2: HS256 needs a key >= its hash output size (32 bytes).
        # PyJWT only warns on a short key — fail startup instead, since a
        # weak signing secret undermines every access token the API issues.
        if len(value.encode()) < 32:
            raise ValueError("jwt_secret_key must be at least 32 bytes (RFC 7518 3.2)")
        return value

    # Dev-only seed defaults; override in .env for anything beyond local dev.
    seed_admin_name: str = "Admin"
    seed_admin_email: str = "admin@ch-tech.dev"
    seed_admin_password: str = "changeme"

    # Optional: unset in local dev skips the actual send (API.md - POST
    # /contact: a failed/absent email provider must never block the request).
    resend_api_key: str | None = None
    contact_notification_email: str | None = None
    contact_notification_from: str = "CH-TECH <onboarding@resend.dev>"


@lru_cache
def get_settings() -> Settings:
    return Settings()
