import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.product_repository import ProductInput
from app.core.errors import ConflictError
from app.domain.enums import ProductStatus
from app.infrastructure.repositories.product_repository import (
    SQLAlchemyProductRepository,
)


def _input(**overrides: object) -> ProductInput:
    defaults: dict[str, object] = {
        "slug": "repo-test",
        "name": "Repo Test",
        "short_description": None,
        "full_description": None,
        "status": ProductStatus.WAITLIST,
    }
    defaults.update(overrides)
    return ProductInput(**defaults)  # type: ignore[arg-type]


async def test_create_persists_and_returns_the_product(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyProductRepository(db_session)

    result = await repo.create(_input(slug="brand-new"))

    assert str(result.slug) == "brand-new"
    assert result.status is ProductStatus.WAITLIST


async def test_create_rejects_a_duplicate_slug(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProductRepository(db_session)
    await repo.create(_input(slug="taken"))

    with pytest.raises(ConflictError):
        await repo.create(_input(slug="taken"))


async def test_list_sorted_by_name(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProductRepository(db_session)
    await repo.create(_input(slug="zeta", name="Zeta"))
    await repo.create(_input(slug="alpha", name="Alpha"))

    result = await repo.list()

    assert [p.name for p in result] == ["Alpha", "Zeta"]


async def test_get_by_slug_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProductRepository(db_session)
    assert await repo.get_by_slug("missing") is None


async def test_update_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProductRepository(db_session)
    assert await repo.update(uuid.uuid4(), _input()) is None


async def test_update_applies_changes(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProductRepository(db_session)
    created = await repo.create(_input(slug="to-update", status=ProductStatus.WAITLIST))

    updated = await repo.update(
        created.id, _input(slug="to-update", status=ProductStatus.LIVE)
    )

    assert updated is not None
    assert updated.status is ProductStatus.LIVE


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProductRepository(db_session)
    assert await repo.delete(uuid.uuid4()) is False


async def test_delete_removes_the_product(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProductRepository(db_session)
    created = await repo.create(_input(slug="to-delete"))

    assert await repo.delete(created.id) is True
    assert await repo.get_by_slug("to-delete") is None


async def test_round_trip_preserves_url_and_logo(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProductRepository(db_session)
    created = await repo.create(
        _input(
            url="https://observability.ch-tech.dev",
            logo="https://ch-tech.dev/products/observability.png",
        )
    )

    fetched = await repo.get_by_slug(str(created.slug))

    assert fetched is not None
    assert str(fetched.url) == "https://observability.ch-tech.dev"
    assert str(fetched.logo) == "https://ch-tech.dev/products/observability.png"
