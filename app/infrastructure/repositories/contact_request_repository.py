"""SQLAlchemy adapter for the ContactRequestRepository port (ADR-0012, Fase 4)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.contact_request_repository import ContactRequestInput
from app.domain.contact_request import ContactRequest as ContactRequestEntity
from app.domain.enums import ContactStatus
from app.domain.value_objects import Email
from app.models import ContactRequest as ContactRequestModel


def _to_entity(model: ContactRequestModel) -> ContactRequestEntity:
    return ContactRequestEntity(
        id=model.id,
        name=model.name,
        email=Email(model.email),
        company=model.company,
        subject=model.subject,
        message=model.message,
        interested_service_line_id=model.interested_service_line_id,
        source=model.source,
        status=ContactStatus(model.status),
        created_at=model.created_at,
    )


class SQLAlchemyContactRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ContactRequestInput) -> ContactRequestEntity:
        model = ContactRequestModel(
            name=data.name,
            email=data.email,
            company=data.company,
            subject=data.subject,
            message=data.message,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)
