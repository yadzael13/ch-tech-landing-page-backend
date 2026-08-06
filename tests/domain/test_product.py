import uuid
from datetime import UTC, datetime

from app.domain.enums import ProductStatus
from app.domain.product import Product
from app.domain.value_objects import Image, Slug, Url


def _product(**overrides: object) -> Product:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "slug": Slug("ch-tech-observability"),
        "name": "CH-TECH Observability",
        "short_description": None,
        "full_description": None,
        "status": ProductStatus.WAITLIST,
        "url": None,
        "logo": None,
        "featured": False,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Product(**defaults)  # type: ignore[arg-type]


def test_product_holds_a_slug_value_object() -> None:
    assert str(_product().slug) == "ch-tech-observability"


def test_product_url_and_logo_are_value_objects_when_present() -> None:
    product = _product(
        url=Url("https://observability.ch-tech.dev"),
        logo=Image("https://ch-tech.dev/products/observability.png"),
    )
    assert isinstance(product.url, Url)
    assert isinstance(product.logo, Image)


def test_product_defaults_to_waitlist_status() -> None:
    assert _product().status is ProductStatus.WAITLIST
