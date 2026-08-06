import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.application.ports.partner_repository import PartnerInput
from app.application.use_cases.partners import (
    CreatePartner,
    DeletePartner,
    ListPartners,
    UpdatePartner,
)
from app.core.rate_limit import ip_rate_limiter
from app.db.session import get_db
from app.domain.partner import Partner
from app.infrastructure.repositories.partner_repository import (
    SQLAlchemyPartnerRepository,
)
from app.schemas.partner import PartnerItem, PartnerWrite
from app.schemas.response import SuccessResponse

public_router = APIRouter(prefix="/partners", tags=["partners"])
admin_router = APIRouter(prefix="/admin/partners", tags=["admin:partners"])

# API.md "Rate Limiting" -> "API Pública": 100 requests/minute/IP.
_public_api_limit = Depends(
    ip_rate_limiter(limit=100, window_seconds=60, scope="public-api")
)

# Admin writes are auth-gated but otherwise had no throttle — a leaked
# access token could hammer these without limit (OWASP API4:2023).
_admin_write_limit = Depends(
    ip_rate_limiter(limit=60, window_seconds=60, scope="admin-write")
)


def _list_use_case(session: AsyncSession = Depends(get_db)) -> ListPartners:
    return ListPartners(repository=SQLAlchemyPartnerRepository(session))


def _create_use_case(session: AsyncSession = Depends(get_db)) -> CreatePartner:
    return CreatePartner(repository=SQLAlchemyPartnerRepository(session))


def _update_use_case(session: AsyncSession = Depends(get_db)) -> UpdatePartner:
    return UpdatePartner(repository=SQLAlchemyPartnerRepository(session))


def _delete_use_case(session: AsyncSession = Depends(get_db)) -> DeletePartner:
    return DeletePartner(repository=SQLAlchemyPartnerRepository(session))


def _to_item(partner: Partner) -> PartnerItem:
    return PartnerItem(
        id=partner.id,
        name=partner.name,
        logo=str(partner.logo) if partner.logo else None,
        partnership_type=partner.partnership_type,
        website_url=str(partner.website_url) if partner.website_url else None,
        created_at=partner.created_at,
        updated_at=partner.updated_at,
    )


def _to_input(payload: PartnerWrite) -> PartnerInput:
    return PartnerInput(
        name=payload.name,
        logo=payload.logo,
        partnership_type=payload.partnership_type,
        website_url=payload.website_url,
    )


@public_router.get("", dependencies=[_public_api_limit])
async def list_partners(
    use_case: ListPartners = Depends(_list_use_case),
) -> SuccessResponse[list[PartnerItem]]:
    partners = await use_case.execute()
    return SuccessResponse(data=[_to_item(p) for p in partners])


@admin_router.post("", status_code=201, dependencies=[_admin_write_limit])
async def create_partner(
    payload: PartnerWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: CreatePartner = Depends(_create_use_case),
) -> SuccessResponse[PartnerItem]:
    partner = await use_case.execute(_to_input(payload))
    return SuccessResponse(data=_to_item(partner))


@admin_router.put("/{partner_id}", dependencies=[_admin_write_limit])
async def update_partner(
    partner_id: uuid.UUID,
    payload: PartnerWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: UpdatePartner = Depends(_update_use_case),
) -> SuccessResponse[PartnerItem]:
    partner = await use_case.execute(partner_id, _to_input(payload))
    return SuccessResponse(data=_to_item(partner))


@admin_router.delete(
    "/{partner_id}", status_code=204, dependencies=[_admin_write_limit]
)
async def delete_partner(
    partner_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: DeletePartner = Depends(_delete_use_case),
) -> None:
    await use_case.execute(partner_id)
