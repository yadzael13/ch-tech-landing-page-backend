import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.api.v1.contact as contact_module
from app.core.rate_limit import get_redis
from app.domain.contact_request import ContactRequest
from app.main import app
from app.models import ContactRequest as ContactRequestModel

_VALID_PAYLOAD = {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "company": "Analytical Engines Inc",
    "subject": "Let's talk",
    "message": "A message that is definitely long enough to be valid.",
}


async def test_submit_contact_request_persists_and_returns_message(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _noop(_contact: ContactRequest) -> None:
        return None

    monkeypatch.setattr(contact_module, "send_contact_notification_email", _noop)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/contact", json=_VALID_PAYLOAD)

    assert response.status_code == 201
    assert response.json() == {"message": "Contact request received."}

    result = await db_session.execute(
        select(ContactRequestModel).where(
            ContactRequestModel.email == "ada@example.com"
        )
    )
    contact = result.scalar_one()
    assert contact.status == "NEW"
    assert contact.name == "Ada Lovelace"


@pytest.mark.usefixtures("db_session")
async def test_submit_contact_request_schedules_notification_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[ContactRequest] = []

    async def _fake_send(contact: ContactRequest) -> None:
        calls.append(contact)

    monkeypatch.setattr(contact_module, "send_contact_notification_email", _fake_send)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/contact", json=_VALID_PAYLOAD)

    assert response.status_code == 201
    assert len(calls) == 1
    assert str(calls[0].email) == "ada@example.com"


@pytest.mark.usefixtures("db_session")
async def test_submit_contact_request_rejects_invalid_email() -> None:
    payload = {**_VALID_PAYLOAD, "email": "not-an-email"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/contact", json=payload)

    assert response.status_code == 422


@pytest.mark.usefixtures("db_session")
async def test_submit_contact_request_rejects_short_message() -> None:
    payload = {**_VALID_PAYLOAD, "message": "too short"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/contact", json=payload)

    assert response.status_code == 422


@pytest.mark.usefixtures("db_session")
async def test_submit_contact_request_rejects_long_message() -> None:
    payload = {**_VALID_PAYLOAD, "message": "x" * 5001}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/contact", json=payload)

    assert response.status_code == 422


@pytest.mark.usefixtures("db_session")
async def test_submit_contact_request_is_rate_limited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _noop(_contact: ContactRequest) -> None:
        return None

    monkeypatch.setattr(contact_module, "send_contact_notification_email", _noop)

    # This exact key is shared by every other test in this file (keyed by
    # client IP, not per-test data) — start this test's own 10-request
    # budget from zero regardless of what they used.
    await get_redis().delete("ratelimit:contact:127.0.0.1")

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(10):
                response = await client.post("/api/v1/contact", json=_VALID_PAYLOAD)
                assert response.status_code == 201

            over_limit = await client.post("/api/v1/contact", json=_VALID_PAYLOAD)

        assert over_limit.status_code == 429
    finally:
        await get_redis().delete("ratelimit:contact:127.0.0.1")
