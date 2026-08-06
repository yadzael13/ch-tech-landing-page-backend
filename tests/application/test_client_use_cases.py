import uuid
from datetime import UTC, datetime

import pytest

from app.application.ports.client_repository import ClientInput
from app.application.use_cases.clients import (
    CreateClient,
    DeleteClient,
    ListClients,
    UpdateClient,
)
from app.core.errors import ResourceNotFoundError
from app.domain.client import Client
from tests.application.fakes import InMemoryClientRepository


def _client(**overrides: object) -> Client:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "name": "Acme Corp",
        "logo": None,
        "industry": None,
        "website_url": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Client(**defaults)  # type: ignore[arg-type]


def _input(**overrides: object) -> ClientInput:
    defaults: dict[str, object] = {"name": "New Client"}
    defaults.update(overrides)
    return ClientInput(**defaults)  # type: ignore[arg-type]


async def test_list_clients_sorted_by_name() -> None:
    zeta = _client(name="Zeta Inc")
    acme = _client(name="Acme Corp")
    repo = InMemoryClientRepository([zeta, acme])
    use_case = ListClients(repository=repo)

    result = await use_case.execute()

    assert [c.name for c in result] == ["Acme Corp", "Zeta Inc"]


async def test_create_client_persists_it() -> None:
    repo = InMemoryClientRepository()
    use_case = CreateClient(repository=repo)

    result = await use_case.execute(_input(name="Brand New"))

    assert result.name == "Brand New"


async def test_update_client_raises_not_found_when_missing() -> None:
    use_case = UpdateClient(repository=InMemoryClientRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4(), _input())


async def test_update_client_applies_changes() -> None:
    client = _client(name="Old Name")
    repo = InMemoryClientRepository([client])
    use_case = UpdateClient(repository=repo)

    result = await use_case.execute(client.id, _input(name="New Name"))

    assert result.name == "New Name"


async def test_delete_client_raises_not_found_when_missing() -> None:
    use_case = DeleteClient(repository=InMemoryClientRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_delete_client_removes_it() -> None:
    client = _client()
    repo = InMemoryClientRepository([client])
    use_case = DeleteClient(repository=repo)

    await use_case.execute(client.id)

    assert await repo.get_by_id(client.id) is None
