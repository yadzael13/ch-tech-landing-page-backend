import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.application.ports.service_repository import ServiceInput
from app.application.use_cases.services import (
    CreateService,
    DeleteService,
    GetServiceById,
    GetServiceBySlug,
    ListServices,
    UpdateService,
)
from app.core.rate_limit import ip_rate_limiter
from app.db.session import get_db
from app.domain.service import Service
from app.infrastructure.repositories.service_repository import (
    SQLAlchemyServiceRepository,
)
from app.schemas.response import SuccessResponse
from app.schemas.service import ServiceItem, ServiceWrite

public_router = APIRouter(prefix="/services", tags=["services"])
admin_router = APIRouter(prefix="/admin/services", tags=["admin:services"])

# API.md "Rate Limiting" -> "API Pública": 100 requests/minute/IP.
_public_api_limit = Depends(
    ip_rate_limiter(limit=100, window_seconds=60, scope="public-api")
)

# Admin writes are auth-gated but otherwise had no throttle — a leaked
# access token could hammer these without limit (OWASP API4:2023).
_admin_write_limit = Depends(
    ip_rate_limiter(limit=60, window_seconds=60, scope="admin-write")
)


def _list_use_case(session: AsyncSession = Depends(get_db)) -> ListServices:
    return ListServices(repository=SQLAlchemyServiceRepository(session))


def _get_by_slug_use_case(session: AsyncSession = Depends(get_db)) -> GetServiceBySlug:
    return GetServiceBySlug(repository=SQLAlchemyServiceRepository(session))


def _get_by_id_use_case(session: AsyncSession = Depends(get_db)) -> GetServiceById:
    return GetServiceById(repository=SQLAlchemyServiceRepository(session))


def _create_use_case(session: AsyncSession = Depends(get_db)) -> CreateService:
    return CreateService(repository=SQLAlchemyServiceRepository(session))


def _update_use_case(session: AsyncSession = Depends(get_db)) -> UpdateService:
    return UpdateService(repository=SQLAlchemyServiceRepository(session))


def _delete_use_case(session: AsyncSession = Depends(get_db)) -> DeleteService:
    return DeleteService(repository=SQLAlchemyServiceRepository(session))


def _to_item(service: Service) -> ServiceItem:
    return ServiceItem(
        id=service.id,
        slug=str(service.slug),
        title=service.title,
        description=service.description,
        featured=service.featured,
        active=service.active,
        created_at=service.created_at,
        updated_at=service.updated_at,
    )


def _to_input(payload: ServiceWrite) -> ServiceInput:
    return ServiceInput(
        slug=payload.slug,
        title=payload.title,
        description=payload.description,
        featured=payload.featured,
        active=payload.active,
    )


@public_router.get("", dependencies=[_public_api_limit])
async def list_services(
    use_case: ListServices = Depends(_list_use_case),
) -> SuccessResponse[list[ServiceItem]]:
    services = await use_case.execute(active_only=True)
    return SuccessResponse(data=[_to_item(s) for s in services])


@public_router.get("/{slug}", dependencies=[_public_api_limit])
async def get_service(
    slug: str, use_case: GetServiceBySlug = Depends(_get_by_slug_use_case)
) -> SuccessResponse[ServiceItem]:
    service = await use_case.execute(slug, active_only=True)
    return SuccessResponse(data=_to_item(service))


@admin_router.get("")
async def list_admin_services(
    _current_user_id: str = Depends(get_current_user_id),
    use_case: ListServices = Depends(_list_use_case),
) -> SuccessResponse[list[ServiceItem]]:
    """Same shape as GET /services, minus the active=True filter — the admin
    management table needs to see inactive/draft services too."""
    services = await use_case.execute(active_only=False)
    return SuccessResponse(data=[_to_item(s) for s in services])


@admin_router.get("/{service_id}")
async def get_admin_service(
    service_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: GetServiceById = Depends(_get_by_id_use_case),
) -> SuccessResponse[ServiceItem]:
    """Same shape as GET /services/{slug}, but by id and without the
    active=True filter — lets the edit form load an inactive service the
    public detail endpoint would 404 on."""
    service = await use_case.execute(service_id)
    return SuccessResponse(data=_to_item(service))


@admin_router.post("", status_code=201, dependencies=[_admin_write_limit])
async def create_service(
    payload: ServiceWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: CreateService = Depends(_create_use_case),
) -> SuccessResponse[ServiceItem]:
    service = await use_case.execute(_to_input(payload))
    return SuccessResponse(data=_to_item(service))


@admin_router.put("/{service_id}", dependencies=[_admin_write_limit])
async def update_service(
    service_id: uuid.UUID,
    payload: ServiceWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: UpdateService = Depends(_update_use_case),
) -> SuccessResponse[ServiceItem]:
    service = await use_case.execute(service_id, _to_input(payload))
    return SuccessResponse(data=_to_item(service))


@admin_router.delete(
    "/{service_id}", status_code=204, dependencies=[_admin_write_limit]
)
async def delete_service(
    service_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: DeleteService = Depends(_delete_use_case),
) -> None:
    await use_case.execute(service_id)
