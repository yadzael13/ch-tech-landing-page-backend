import uuid
from datetime import UTC, datetime

from app.domain.contact_request import ContactRequest
from app.domain.enums import ContactStatus
from app.domain.value_objects import Email


def _contact_request(**overrides: object) -> ContactRequest:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "name": "Ada Lovelace",
        "email": Email("ada@example.com"),
        "company": None,
        "subject": None,
        "message": "We'd like to talk about an automation project.",
        "interested_service_line_id": None,
        "source": None,
        "status": ContactStatus.NEW,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return ContactRequest(**defaults)  # type: ignore[arg-type]


def test_contact_request_defaults_to_new_status() -> None:
    assert _contact_request().status is ContactStatus.NEW


def test_contact_request_holds_an_email_value_object() -> None:
    assert isinstance(_contact_request().email, Email)


def test_contact_request_interest_and_source_are_optional() -> None:
    request = _contact_request()
    assert request.interested_service_line_id is None
    assert request.source is None


def test_contact_request_can_declare_a_service_line_of_interest() -> None:
    service_line_id = uuid.uuid4()
    request = _contact_request(
        interested_service_line_id=service_line_id, source="landing_form"
    )
    assert request.interested_service_line_id == service_line_id
    assert request.source == "landing_form"
