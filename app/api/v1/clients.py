import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.application.ports.client_repository import ClientInput
from app.application.use_cases.clients import (
    CreateClient,
    DeleteClient,
    ListClients,
    UpdateClient,
)
from app.core.rate_limit import ip_rate_limiter
from app.db.session import get_db
from app.domain.client import Client
from app.infrastructure.repositories.client_repository import (
    SQLAlchemyClientRepository,
)
from app.schemas.client import ClientItem, ClientWrite
from app.schemas.response import SuccessResponse

public_router = APIRouter(prefix="/clients", tags=["clients"])
admin_router = APIRouter(prefix="/admin/clients", tags=["admin:clients"])

# API.md "Rate Limiting" -> "API Pública": 100 requests/minute/IP.
_public_api_limit = Depends(
    ip_rate_limiter(limit=100, window_seconds=60, scope="public-api")
)

# Admin writes are auth-gated but otherwise had no throttle — a leaked
# access token could hammer these without limit (OWASP API4:2023).
_admin_write_limit = Depends(
    ip_rate_limiter(limit=60, window_seconds=60, scope="admin-write")
)


def _list_use_case(session: AsyncSession = Depends(get_db)) -> ListClients:
    return ListClients(repository=SQLAlchemyClientRepository(session))


def _create_use_case(session: AsyncSession = Depends(get_db)) -> CreateClient:
    return CreateClient(repository=SQLAlchemyClientRepository(session))


def _update_use_case(session: AsyncSession = Depends(get_db)) -> UpdateClient:
    return UpdateClient(repository=SQLAlchemyClientRepository(session))


def _delete_use_case(session: AsyncSession = Depends(get_db)) -> DeleteClient:
    return DeleteClient(repository=SQLAlchemyClientRepository(session))


def _to_item(client: Client) -> ClientItem:
    return ClientItem(
        id=client.id,
        name=client.name,
        logo=str(client.logo) if client.logo else None,
        industry=client.industry,
        website_url=str(client.website_url) if client.website_url else None,
        created_at=client.created_at,
        updated_at=client.updated_at,
    )


def _to_input(payload: ClientWrite) -> ClientInput:
    return ClientInput(
        name=payload.name,
        logo=payload.logo,
        industry=payload.industry,
        website_url=payload.website_url,
    )


@public_router.get("", dependencies=[_public_api_limit])
async def list_clients(
    use_case: ListClients = Depends(_list_use_case),
) -> SuccessResponse[list[ClientItem]]:
    clients = await use_case.execute()
    return SuccessResponse(data=[_to_item(c) for c in clients])


@admin_router.post("", status_code=201, dependencies=[_admin_write_limit])
async def create_client(
    payload: ClientWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: CreateClient = Depends(_create_use_case),
) -> SuccessResponse[ClientItem]:
    client = await use_case.execute(_to_input(payload))
    return SuccessResponse(data=_to_item(client))


@admin_router.put("/{client_id}", dependencies=[_admin_write_limit])
async def update_client(
    client_id: uuid.UUID,
    payload: ClientWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: UpdateClient = Depends(_update_use_case),
) -> SuccessResponse[ClientItem]:
    client = await use_case.execute(client_id, _to_input(payload))
    return SuccessResponse(data=_to_item(client))


@admin_router.delete("/{client_id}", status_code=204, dependencies=[_admin_write_limit])
async def delete_client(
    client_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: DeleteClient = Depends(_delete_use_case),
) -> None:
    await use_case.execute(client_id)
