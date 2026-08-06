import uuid
from datetime import UTC, datetime

from app.domain.testimonial import Testimonial


def _testimonial(**overrides: object) -> Testimonial:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "author_name": "Ada Lovelace",
        "author_role": "CTO",
        "client_id": None,
        "project_id": None,
        "content": "CH-TECH delivered exactly what we needed.",
        "rating": None,
        "featured": False,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Testimonial(**defaults)  # type: ignore[arg-type]


def test_testimonial_can_exist_without_a_client_or_project() -> None:
    testimonial = _testimonial(client_id=None, project_id=None)
    assert testimonial.client_id is None
    assert testimonial.project_id is None


def test_testimonial_can_reference_a_client_and_project() -> None:
    client_id = uuid.uuid4()
    project_id = uuid.uuid4()
    testimonial = _testimonial(client_id=client_id, project_id=project_id)
    assert testimonial.client_id == client_id
    assert testimonial.project_id == project_id
