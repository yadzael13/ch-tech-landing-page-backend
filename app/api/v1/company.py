from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.application.ports.company_repository import CompanyInput
from app.application.use_cases.company import GetCompany, UpdateCompany
from app.core.rate_limit import ip_rate_limiter
from app.db.session import get_db
from app.domain.company import Company
from app.infrastructure.repositories.company_repository import (
    SQLAlchemyCompanyRepository,
)
from app.schemas.company import CompanyItem, CompanyWrite
from app.schemas.response import SuccessResponse

public_router = APIRouter(tags=["company"])
admin_router = APIRouter(prefix="/admin", tags=["admin:company"])

# API.md "Rate Limiting" -> "API Pública": 100 requests/minute/IP.
_public_api_limit = Depends(
    ip_rate_limiter(limit=100, window_seconds=60, scope="public-api")
)

# Admin writes are auth-gated but otherwise had no throttle — a leaked
# access token could hammer these without limit (OWASP API4:2023).
_admin_write_limit = Depends(
    ip_rate_limiter(limit=60, window_seconds=60, scope="admin-write")
)


def _get_use_case(session: AsyncSession = Depends(get_db)) -> GetCompany:
    return GetCompany(repository=SQLAlchemyCompanyRepository(session))


def _update_use_case(session: AsyncSession = Depends(get_db)) -> UpdateCompany:
    return UpdateCompany(repository=SQLAlchemyCompanyRepository(session))


def _to_item(company: Company) -> CompanyItem:
    return CompanyItem(
        id=company.id,
        legal_name=company.legal_name,
        display_name=company.display_name,
        tagline=company.tagline,
        mission=company.mission,
        vision=company.vision,
        email=str(company.email) if company.email else None,
        phone=company.phone,
        address=company.address,
        social_links=company.social_links,
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


def _to_input(payload: CompanyWrite) -> CompanyInput:
    return CompanyInput(
        legal_name=payload.legal_name,
        display_name=payload.display_name,
        tagline=payload.tagline,
        mission=payload.mission,
        vision=payload.vision,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        social_links=payload.social_links,
    )


@public_router.get("/company", dependencies=[_public_api_limit])
async def get_company(
    use_case: GetCompany = Depends(_get_use_case),
) -> SuccessResponse[CompanyItem]:
    company = await use_case.execute()
    return SuccessResponse(data=_to_item(company))


@admin_router.put("/company", dependencies=[_admin_write_limit])
async def update_company(
    payload: CompanyWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: UpdateCompany = Depends(_update_use_case),
) -> SuccessResponse[CompanyItem]:
    company = await use_case.execute(_to_input(payload))
    return SuccessResponse(data=_to_item(company))
