from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.contact_request_repository import ContactRequestInput
from app.domain.enums import ContactStatus
from app.infrastructure.repositories.contact_request_repository import (
    SQLAlchemyContactRequestRepository,
)


def _input(**overrides: object) -> ContactRequestInput:
    defaults: dict[str, object] = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "company": "Acme",
        "subject": "Automation",
        "message": "We'd like to talk about an automation project.",
    }
    defaults.update(overrides)
    return ContactRequestInput(**defaults)  # type: ignore[arg-type]


async def test_create_persists_and_returns_the_contact_request(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyContactRequestRepository(db_session)

    result = await repo.create(_input())

    assert result.name == "Ada Lovelace"
    assert str(result.email) == "ada@example.com"
    assert result.status is ContactStatus.NEW
    assert result.id is not None
