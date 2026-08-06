import uuid
from datetime import UTC, datetime

import pytest

from app.application.ports.partner_repository import PartnerInput
from app.application.use_cases.partners import (
    CreatePartner,
    DeletePartner,
    ListPartners,
    UpdatePartner,
)
from app.core.errors import ResourceNotFoundError
from app.domain.partner import Partner
from tests.application.fakes import InMemoryPartnerRepository


def _partner(**overrides: object) -> Partner:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "name": "Amazon Web Services",
        "logo": None,
        "partnership_type": None,
        "website_url": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Partner(**defaults)  # type: ignore[arg-type]


def _input(**overrides: object) -> PartnerInput:
    defaults: dict[str, object] = {"name": "New Partner"}
    defaults.update(overrides)
    return PartnerInput(**defaults)  # type: ignore[arg-type]


async def test_list_partners_sorted_by_name() -> None:
    zeta = _partner(name="Zeta Cloud")
    aws = _partner(name="Amazon Web Services")
    repo = InMemoryPartnerRepository([zeta, aws])
    use_case = ListPartners(repository=repo)

    result = await use_case.execute()

    assert [p.name for p in result] == ["Amazon Web Services", "Zeta Cloud"]


async def test_create_partner_persists_it() -> None:
    repo = InMemoryPartnerRepository()
    use_case = CreatePartner(repository=repo)

    result = await use_case.execute(_input(name="Brand New"))

    assert result.name == "Brand New"


async def test_update_partner_raises_not_found_when_missing() -> None:
    use_case = UpdatePartner(repository=InMemoryPartnerRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4(), _input())


async def test_update_partner_applies_changes() -> None:
    partner = _partner(name="Old Name")
    repo = InMemoryPartnerRepository([partner])
    use_case = UpdatePartner(repository=repo)

    result = await use_case.execute(partner.id, _input(name="New Name"))

    assert result.name == "New Name"


async def test_delete_partner_raises_not_found_when_missing() -> None:
    use_case = DeletePartner(repository=InMemoryPartnerRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_delete_partner_removes_it() -> None:
    partner = _partner()
    repo = InMemoryPartnerRepository([partner])
    use_case = DeletePartner(repository=repo)

    await use_case.execute(partner.id)

    assert await repo.get_by_id(partner.id) is None
