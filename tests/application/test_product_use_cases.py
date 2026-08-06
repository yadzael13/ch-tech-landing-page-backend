import uuid
from datetime import UTC, datetime

import pytest

from app.application.ports.product_repository import ProductInput
from app.application.use_cases.products import (
    CreateProduct,
    DeleteProduct,
    GetProductBySlug,
    ListProducts,
    UpdateProduct,
)
from app.core.errors import ConflictError, ResourceNotFoundError
from app.domain.enums import ProductStatus
from app.domain.product import Product
from app.domain.value_objects import Slug
from tests.application.fakes import InMemoryProductRepository


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


def _input(**overrides: object) -> ProductInput:
    defaults: dict[str, object] = {
        "slug": "new-product",
        "name": "New Product",
        "short_description": None,
        "full_description": None,
        "status": ProductStatus.WAITLIST,
    }
    defaults.update(overrides)
    return ProductInput(**defaults)  # type: ignore[arg-type]


async def test_list_products_sorted_by_name() -> None:
    zeta = _product(slug=Slug("zeta"), name="Zeta")
    alpha = _product(slug=Slug("alpha"), name="Alpha")
    repo = InMemoryProductRepository([zeta, alpha])
    use_case = ListProducts(repository=repo)

    result = await use_case.execute()

    assert [p.name for p in result] == ["Alpha", "Zeta"]


async def test_get_product_by_slug_raises_not_found_when_missing() -> None:
    use_case = GetProductBySlug(repository=InMemoryProductRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute("missing")


async def test_create_product_defaults_to_waitlist() -> None:
    repo = InMemoryProductRepository()
    use_case = CreateProduct(repository=repo)

    result = await use_case.execute(_input(slug="brand-new"))

    assert result.status is ProductStatus.WAITLIST


async def test_create_product_rejects_a_duplicate_slug() -> None:
    repo = InMemoryProductRepository([_product(slug=Slug("taken"))])
    use_case = CreateProduct(repository=repo)

    with pytest.raises(ConflictError):
        await use_case.execute(_input(slug="taken"))


async def test_update_product_raises_not_found_when_missing() -> None:
    use_case = UpdateProduct(repository=InMemoryProductRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4(), _input())


async def test_update_product_applies_changes() -> None:
    product = _product(status=ProductStatus.WAITLIST)
    repo = InMemoryProductRepository([product])
    use_case = UpdateProduct(repository=repo)

    result = await use_case.execute(
        product.id,
        _input(slug=str(product.slug), status=ProductStatus.LIVE),
    )

    assert result.status is ProductStatus.LIVE


async def test_delete_product_raises_not_found_when_missing() -> None:
    use_case = DeleteProduct(repository=InMemoryProductRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_delete_product_removes_it() -> None:
    product = _product()
    repo = InMemoryProductRepository([product])
    use_case = DeleteProduct(repository=repo)

    await use_case.execute(product.id)

    assert await repo.get_by_slug(str(product.slug)) is None
