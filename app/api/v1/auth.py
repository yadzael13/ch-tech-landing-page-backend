import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.application.use_cases.auth import AuthTokens, Login, Logout, RefreshAccessToken
from app.core.config import get_settings
from app.core.rate_limit import check_rate_limit, ip_rate_limiter
from app.db.session import get_db
from app.infrastructure.repositories.refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Refresh tokens are 32-byte random values (unguessable), but the endpoint
# still had zero throttle — cap it to bound abuse/resource consumption
# (OWASP API4:2023), independent of the per-email login limiter above.
_refresh_rate_limit = Depends(
    ip_rate_limiter(limit=20, window_seconds=60, scope="refresh")
)


def _login_use_case(session: AsyncSession = Depends(get_db)) -> Login:
    return Login(
        user_repository=SQLAlchemyUserRepository(session),
        refresh_token_repository=SQLAlchemyRefreshTokenRepository(session),
        refresh_token_ttl=timedelta(days=get_settings().refresh_token_expire_days),
    )


def _logout_use_case(session: AsyncSession = Depends(get_db)) -> Logout:
    return Logout(refresh_token_repository=SQLAlchemyRefreshTokenRepository(session))


def _refresh_use_case(session: AsyncSession = Depends(get_db)) -> RefreshAccessToken:
    return RefreshAccessToken(
        user_repository=SQLAlchemyUserRepository(session),
        refresh_token_repository=SQLAlchemyRefreshTokenRepository(session),
        refresh_token_ttl=timedelta(days=get_settings().refresh_token_expire_days),
    )


def _to_response(tokens: AuthTokens) -> TokenResponse:
    return TokenResponse(
        access_token=tokens.access_token, refresh_token=tokens.refresh_token
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    use_case: Login = Depends(_login_use_case),
) -> TokenResponse:
    # Keyed by email, not IP (API.md is the only one of the three documented
    # limits that omits "/IP") — this is what actually stops brute-forcing
    # one account, since an attacker can trivially rotate source IPs.
    await check_rate_limit(
        f"ratelimit:login:{payload.email.lower()}", limit=5, window_seconds=900
    )

    tokens = await use_case.execute(
        email=payload.email,
        password=payload.password,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    return _to_response(tokens)


@router.post("/logout", status_code=204)
async def logout(
    payload: RefreshRequest,
    current_user_id: str = Depends(get_current_user_id),
    use_case: Logout = Depends(_logout_use_case),
) -> None:
    await use_case.execute(
        raw_refresh_token=payload.refresh_token,
        current_user_id=uuid.UUID(current_user_id),
    )


@router.post(
    "/refresh", response_model=TokenResponse, dependencies=[_refresh_rate_limit]
)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    use_case: RefreshAccessToken = Depends(_refresh_use_case),
) -> TokenResponse:
    tokens = await use_case.execute(
        raw_refresh_token=payload.refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    return _to_response(tokens)
