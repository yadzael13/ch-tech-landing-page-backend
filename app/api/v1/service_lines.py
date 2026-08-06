import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.application.ports.service_line_repository import ServiceLineInput
from app.application.use_cases.service_lines import (
    CreateServiceLine,
    DeleteServiceLine,
    GetServiceLineBySlug,
    ListServiceLines,
    UpdateServiceLine,
)
from app.core.rate_limit import ip_rate_limiter
from app.db.session import get_db
from app.domain.service_line import ServiceLine
from app.infrastructure.repositories.service_line_repository import (
    SQLAlchemyServiceLineRepository,
)
from app.schemas.response import SuccessResponse
from app.schemas.service_line import ServiceLineItem, ServiceLineWrite

public_router = APIRouter(prefix="/service-lines", tags=["service-lines"])
admin_router = APIRouter(prefix="/admin/service-lines", tags=["admin:service-lines"])

# API.md "Rate Limiting" -> "API Pública": 100 requests/minute/IP.
_public_api_limit = Depends(
    ip_rate_limiter(limit=100, window_seconds=60, scope="public-api")
)

# Admin writes are auth-gated but otherwise had no throttle — a leaked
# access token could hammer these without limit (OWASP API4:2023).
_admin_write_limit = Depends(
    ip_rate_limiter(limit=60, window_seconds=60, scope="admin-write")
)


def _list_use_case(session: AsyncSession = Depends(get_db)) -> ListServiceLines:
    return ListServiceLines(repository=SQLAlchemyServiceLineRepository(session))


def _get_by_slug_use_case(
    session: AsyncSession = Depends(get_db),
) -> GetServiceLineBySlug:
    return GetServiceLineBySlug(repository=SQLAlchemyServiceLineRepository(session))


def _create_use_case(session: AsyncSession = Depends(get_db)) -> CreateServiceLine:
    return CreateServiceLine(repository=SQLAlchemyServiceLineRepository(session))


def _update_use_case(session: AsyncSession = Depends(get_db)) -> UpdateServiceLine:
    return UpdateServiceLine(repository=SQLAlchemyServiceLineRepository(session))


def _delete_use_case(session: AsyncSession = Depends(get_db)) -> DeleteServiceLine:
    return DeleteServiceLine(repository=SQLAlchemyServiceLineRepository(session))


def _to_item(service_line: ServiceLine) -> ServiceLineItem:
    return ServiceLineItem(
        id=service_line.id,
        slug=str(service_line.slug),
        name=service_line.name,
        description=service_line.description,
        icon=str(service_line.icon) if service_line.icon else None,
        display_order=service_line.display_order,
        created_at=service_line.created_at,
        updated_at=service_line.updated_at,
    )


def _to_input(payload: ServiceLineWrite) -> ServiceLineInput:
    return ServiceLineInput(
        slug=payload.slug,
        name=payload.name,
        description=payload.description,
        icon=payload.icon,
        display_order=payload.display_order,
    )


@public_router.get("", dependencies=[_public_api_limit])
async def list_service_lines(
    use_case: ListServiceLines = Depends(_list_use_case),
) -> SuccessResponse[list[ServiceLineItem]]:
    service_lines = await use_case.execute()
    return SuccessResponse(data=[_to_item(s) for s in service_lines])


@public_router.get("/{slug}", dependencies=[_public_api_limit])
async def get_service_line(
    slug: str, use_case: GetServiceLineBySlug = Depends(_get_by_slug_use_case)
) -> SuccessResponse[ServiceLineItem]:
    service_line = await use_case.execute(slug)
    return SuccessResponse(data=_to_item(service_line))


@admin_router.post("", status_code=201, dependencies=[_admin_write_limit])
async def create_service_line(
    payload: ServiceLineWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: CreateServiceLine = Depends(_create_use_case),
) -> SuccessResponse[ServiceLineItem]:
    service_line = await use_case.execute(_to_input(payload))
    return SuccessResponse(data=_to_item(service_line))


@admin_router.put("/{service_line_id}", dependencies=[_admin_write_limit])
async def update_service_line(
    service_line_id: uuid.UUID,
    payload: ServiceLineWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: UpdateServiceLine = Depends(_update_use_case),
) -> SuccessResponse[ServiceLineItem]:
    service_line = await use_case.execute(service_line_id, _to_input(payload))
    return SuccessResponse(data=_to_item(service_line))


@admin_router.delete(
    "/{service_line_id}", status_code=204, dependencies=[_admin_write_limit]
)
async def delete_service_line(
    service_line_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: DeleteServiceLine = Depends(_delete_use_case),
) -> None:
    await use_case.execute(service_line_id)
