import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.application.ports.technology_repository import (
    TechnologyFilters,
    TechnologyInput,
)
from app.application.use_cases.technologies import (
    CreateTechnology,
    DeleteTechnology,
    GetTechnologyById,
    ListTechnologies,
    UpdateTechnology,
)
from app.core.rate_limit import ip_rate_limiter
from app.db.session import get_db
from app.domain.technology import Technology
from app.infrastructure.repositories.technology_repository import (
    SQLAlchemyTechnologyRepository,
)
from app.schemas.response import SuccessResponse
from app.schemas.technology import TechnologyItem, TechnologyWrite

public_router = APIRouter(prefix="/technologies", tags=["technologies"])
admin_router = APIRouter(prefix="/admin/technologies", tags=["admin:technologies"])

# API.md "Rate Limiting" -> "API Pública": 100 requests/minute/IP.
_public_api_limit = Depends(
    ip_rate_limiter(limit=100, window_seconds=60, scope="public-api")
)

# Admin writes are auth-gated but otherwise had no throttle — a leaked
# access token could hammer these without limit (OWASP API4:2023).
_admin_write_limit = Depends(
    ip_rate_limiter(limit=60, window_seconds=60, scope="admin-write")
)


def _list_use_case(session: AsyncSession = Depends(get_db)) -> ListTechnologies:
    return ListTechnologies(repository=SQLAlchemyTechnologyRepository(session))


def _get_by_id_use_case(session: AsyncSession = Depends(get_db)) -> GetTechnologyById:
    return GetTechnologyById(repository=SQLAlchemyTechnologyRepository(session))


def _create_use_case(session: AsyncSession = Depends(get_db)) -> CreateTechnology:
    return CreateTechnology(repository=SQLAlchemyTechnologyRepository(session))


def _update_use_case(session: AsyncSession = Depends(get_db)) -> UpdateTechnology:
    return UpdateTechnology(repository=SQLAlchemyTechnologyRepository(session))


def _delete_use_case(session: AsyncSession = Depends(get_db)) -> DeleteTechnology:
    return DeleteTechnology(repository=SQLAlchemyTechnologyRepository(session))


def _to_item(technology: Technology) -> TechnologyItem:
    return TechnologyItem(
        id=technology.id,
        name=technology.name,
        category=technology.category,
        icon=str(technology.icon) if technology.icon else None,
        official_url=str(technology.official_url) if technology.official_url else None,
        created_at=technology.created_at,
        updated_at=technology.updated_at,
    )


def _to_input(payload: TechnologyWrite) -> TechnologyInput:
    return TechnologyInput(
        name=payload.name,
        category=payload.category,
        icon=payload.icon,
        official_url=payload.official_url,
    )


@public_router.get("", dependencies=[_public_api_limit])
async def list_technologies(
    use_case: ListTechnologies = Depends(_list_use_case),
    category: str | None = None,
) -> SuccessResponse[list[TechnologyItem]]:
    technologies = await use_case.execute(TechnologyFilters(category=category))
    return SuccessResponse(data=[_to_item(t) for t in technologies])


@public_router.get("/{technology_id}", dependencies=[_public_api_limit])
async def get_technology(
    technology_id: uuid.UUID,
    use_case: GetTechnologyById = Depends(_get_by_id_use_case),
) -> SuccessResponse[TechnologyItem]:
    technology = await use_case.execute(technology_id)
    return SuccessResponse(data=_to_item(technology))


@admin_router.post("", status_code=201, dependencies=[_admin_write_limit])
async def create_technology(
    payload: TechnologyWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: CreateTechnology = Depends(_create_use_case),
) -> SuccessResponse[TechnologyItem]:
    technology = await use_case.execute(_to_input(payload))
    return SuccessResponse(data=_to_item(technology))


@admin_router.put("/{technology_id}", dependencies=[_admin_write_limit])
async def update_technology(
    technology_id: uuid.UUID,
    payload: TechnologyWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: UpdateTechnology = Depends(_update_use_case),
) -> SuccessResponse[TechnologyItem]:
    technology = await use_case.execute(technology_id, _to_input(payload))
    return SuccessResponse(data=_to_item(technology))


@admin_router.delete(
    "/{technology_id}", status_code=204, dependencies=[_admin_write_limit]
)
async def delete_technology(
    technology_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: DeleteTechnology = Depends(_delete_use_case),
) -> None:
    await use_case.execute(technology_id)
