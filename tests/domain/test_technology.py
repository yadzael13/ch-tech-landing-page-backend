import uuid
from datetime import UTC, datetime

from app.domain.technology import Technology
from app.domain.value_objects import Image, Url


def _technology(**overrides: object) -> Technology:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "name": "FastAPI",
        "category": "Backend",
        "icon": None,
        "official_url": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Technology(**defaults)  # type: ignore[arg-type]


def test_technology_stores_a_name_and_category() -> None:
    technology = _technology()
    assert technology.name == "FastAPI"
    assert technology.category == "Backend"


def test_technology_icon_and_url_are_value_objects_when_present() -> None:
    technology = _technology(
        icon=Image("https://ch-tech.dev/icons/fastapi.svg"),
        official_url=Url("https://fastapi.tiangolo.com"),
    )
    assert isinstance(technology.icon, Image)
    assert isinstance(technology.official_url, Url)
