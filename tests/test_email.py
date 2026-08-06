import uuid
from datetime import UTC, datetime
from types import TracebackType
from typing import ClassVar

import httpx
import pytest

from app.core import email as email_module
from app.core.config import Settings
from app.domain.contact_request import ContactRequest
from app.domain.enums import ContactStatus
from app.domain.value_objects import Email


def _contact() -> ContactRequest:
    return ContactRequest(
        id=uuid.uuid4(),
        name="Ada Lovelace",
        email=Email("ada@example.com"),
        company="Analytical Engines Inc",
        subject="Let's talk",
        message="A message that is definitely long enough to be valid.",
        interested_service_line_id=None,
        source=None,
        status=ContactStatus.NEW,
        created_at=datetime.now(UTC),
    )


async def test_skips_when_resend_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://u:p@localhost/db",
        redis_url="redis://localhost",
        jwt_secret_key="x" * 32,
    )
    monkeypatch.setattr(email_module, "get_settings", lambda: settings)

    calls = []
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda *a, **kw: calls.append((a, kw)) or None
    )

    await email_module.send_contact_notification_email(_contact())

    assert calls == []


class _FakeAsyncClient:
    last_call: ClassVar[dict[str, object]] = {}

    def __init__(self, status_code: int) -> None:
        self._status_code = status_code

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def post(
        self, url: str, *, json: dict[str, object], headers: dict[str, str]
    ) -> httpx.Response:
        _FakeAsyncClient.last_call = {"url": url, "json": json, "headers": headers}
        return httpx.Response(self._status_code, request=httpx.Request("POST", url))


def _configured_settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://u:p@localhost/db",
        redis_url="redis://localhost",
        jwt_secret_key="x" * 32,
        resend_api_key="re_test_key",
        contact_notification_email="admin@ch-tech.dev",
    )


async def test_posts_to_resend_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(email_module, "get_settings", _configured_settings)
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **_kw: _FakeAsyncClient(status_code=200)
    )

    await email_module.send_contact_notification_email(_contact())

    assert _FakeAsyncClient.last_call["url"] == email_module._RESEND_API_URL
    assert _FakeAsyncClient.last_call["headers"] == {
        "Authorization": "Bearer re_test_key"
    }


async def test_swallows_http_errors_from_resend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(email_module, "get_settings", _configured_settings)
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **_kw: _FakeAsyncClient(status_code=500)
    )

    # Must not raise: a Resend outage can never surface to the caller.
    await email_module.send_contact_notification_email(_contact())
