import uuid
from datetime import UTC, datetime

from app.domain.client import Client
from app.domain.value_objects import Image, Url


def _client(**overrides: object) -> Client:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "name": "Acme Corp",
        "logo": None,
        "industry": None,
        "website_url": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Client(**defaults)  # type: ignore[arg-type]


def test_client_stores_a_name() -> None:
    assert _client(name="Acme Corp").name == "Acme Corp"


def test_client_logo_and_url_are_value_objects_when_present() -> None:
    client = _client(
        logo=Image("https://ch-tech.dev/clients/acme.png"),
        website_url=Url("https://acme.example.com"),
    )
    assert isinstance(client.logo, Image)
    assert isinstance(client.website_url, Url)
