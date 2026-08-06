import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact_request import ContactRequest, ContactStatus


async def test_contact_request_defaults(db_session: AsyncSession) -> None:
    request = ContactRequest(
        name="Jane Doe", email="jane@example.com", message="Hi, I need a website."
    )
    db_session.add(request)
    await db_session.commit()

    assert request.status == ContactStatus.NEW.value
    assert request.created_at is not None
    assert not hasattr(request, "updated_at")


async def test_contact_request_rejects_invalid_status(
    db_session: AsyncSession,
) -> None:
    db_session.add(
        ContactRequest(
            name="Jane",
            email="jane@example.com",
            message="Hi",
            status="NOT_A_STATUS",
        )
    )
    # MySQL raises CHECK constraint violations as OperationalError (error
    # 3819), not IntegrityError like Postgres.
    with pytest.raises(OperationalError):
        await db_session.commit()
