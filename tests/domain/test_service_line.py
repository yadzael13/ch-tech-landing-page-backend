import uuid
from datetime import UTC, datetime

from app.domain.service_line import ServiceLine
from app.domain.value_objects import Image, Slug


def _service_line(**overrides: object) -> ServiceLine:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "slug": Slug("software-engineering"),
        "name": "Software Engineering",
        "description": None,
        "icon": None,
        "display_order": 0,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return ServiceLine(**defaults)  # type: ignore[arg-type]


def test_service_line_holds_a_slug_value_object() -> None:
    assert str(_service_line().slug) == "software-engineering"


def test_service_line_icon_is_a_value_object_when_present() -> None:
    line = _service_line(icon=Image("https://ch-tech.dev/icons/software.svg"))
    assert isinstance(line.icon, Image)
