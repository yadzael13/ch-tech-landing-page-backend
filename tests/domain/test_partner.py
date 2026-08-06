import uuid
from datetime import UTC, datetime

from app.domain.partner import Partner
from app.domain.value_objects import Image, Url


def _partner(**overrides: object) -> Partner:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "name": "Amazon Web Services",
        "logo": None,
        "partnership_type": None,
        "website_url": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Partner(**defaults)  # type: ignore[arg-type]


def test_partner_stores_a_name() -> None:
    assert _partner(name="Amazon Web Services").name == "Amazon Web Services"


def test_partner_logo_and_url_are_value_objects_when_present() -> None:
    partner = _partner(
        logo=Image("https://ch-tech.dev/partners/aws.png"),
        website_url=Url("https://aws.amazon.com"),
    )
    assert isinstance(partner.logo, Image)
    assert isinstance(partner.website_url, Url)
