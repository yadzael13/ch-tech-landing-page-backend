import uuid
from datetime import UTC, datetime

from app.domain.service import Service
from app.domain.value_objects import Slug


def _service(**overrides: object) -> Service:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "service_line_id": uuid.uuid4(),
        "title": "Automatización con IA",
        "slug": Slug("automatizacion-ia"),
        "description": None,
        "featured": False,
        "active": True,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Service(**defaults)  # type: ignore[arg-type]


def test_service_belongs_to_a_service_line() -> None:
    service_line_id = uuid.uuid4()
    assert _service(service_line_id=service_line_id).service_line_id == service_line_id


def test_service_can_have_no_service_line_yet() -> None:
    # services.service_line_id does not exist until Fase 5 (DATABASE_SCHEMA.md).
    assert _service(service_line_id=None).service_line_id is None


def test_service_holds_a_slug_value_object() -> None:
    assert str(_service().slug) == "automatizacion-ia"
