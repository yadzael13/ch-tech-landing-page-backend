from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.contact_request_repository import ContactRequestInput
from app.application.use_cases.contact_requests import SubmitContactRequest
from app.core.email import send_contact_notification_email
from app.core.rate_limit import ip_rate_limiter
from app.db.session import get_db
from app.infrastructure.repositories.contact_request_repository import (
    SQLAlchemyContactRequestRepository,
)
from app.schemas.contact import ContactCreate, ContactReceived

router = APIRouter(tags=["contact"])

# API.md "Rate Limiting" -> POST /contact: 10 requests/hour/IP.
_contact_rate_limit = Depends(
    ip_rate_limiter(limit=10, window_seconds=3600, scope="contact")
)


def _submit_use_case(
    session: AsyncSession = Depends(get_db),
) -> SubmitContactRequest:
    return SubmitContactRequest(repository=SQLAlchemyContactRequestRepository(session))


@router.post("/contact", status_code=201, dependencies=[_contact_rate_limit])
async def submit_contact_request(
    payload: ContactCreate,
    background_tasks: BackgroundTasks,
    use_case: SubmitContactRequest = Depends(_submit_use_case),
) -> ContactReceived:
    contact = await use_case.execute(
        ContactRequestInput(
            name=payload.name,
            email=payload.email,
            company=payload.company,
            subject=payload.subject,
            message=payload.message,
        )
    )

    # Scheduled, not awaited: a Resend outage must never block or fail this
    # response (API.md - POST /contact "Efecto").
    background_tasks.add_task(send_contact_notification_email, contact)

    return ContactReceived()
