from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    # max_length=72: bcrypt's hard limit. Without this, a >72-byte password
    # against an existing email raises inside verify_password() (caught below
    # too, defense in depth) while a nonexistent email short-circuits before
    # ever calling bcrypt — a 500-vs-401 oracle for email enumeration.
    password: str = Field(min_length=1, max_length=72)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    """Deliberately unwrapped (no success/data envelope) — API.md documents
    this exact shape for /auth/login and /auth/refresh, matching the OAuth2
    token-endpoint convention FastAPI's own tooling expects."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
