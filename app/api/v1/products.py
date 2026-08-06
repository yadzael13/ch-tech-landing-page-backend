import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.application.ports.product_repository import ProductInput
from app.application.use_cases.products import (
    CreateProduct,
    DeleteProduct,
    GetProductBySlug,
    ListProducts,
    UpdateProduct,
)
from app.core.rate_limit import ip_rate_limiter
from app.db.session import get_db
from app.domain.product import Product
from app.infrastructure.repositories.product_repository import (
    SQLAlchemyProductRepository,
)
from app.schemas.product import ProductItem, ProductWrite
from app.schemas.response import SuccessResponse

public_router = APIRouter(prefix="/products", tags=["products"])
admin_router = APIRouter(prefix="/admin/products", tags=["admin:products"])

# API.md "Rate Limiting" -> "API Pública": 100 requests/minute/IP.
_public_api_limit = Depends(
    ip_rate_limiter(limit=100, window_seconds=60, scope="public-api")
)

# Admin writes are auth-gated but otherwise had no throttle — a leaked
# access token could hammer these without limit (OWASP API4:2023).
_admin_write_limit = Depends(
    ip_rate_limiter(limit=60, window_seconds=60, scope="admin-write")
)


def _list_use_case(session: AsyncSession = Depends(get_db)) -> ListProducts:
    return ListProducts(repository=SQLAlchemyProductRepository(session))


def _get_by_slug_use_case(
    session: AsyncSession = Depends(get_db),
) -> GetProductBySlug:
    return GetProductBySlug(repository=SQLAlchemyProductRepository(session))


def _create_use_case(session: AsyncSession = Depends(get_db)) -> CreateProduct:
    return CreateProduct(repository=SQLAlchemyProductRepository(session))


def _update_use_case(session: AsyncSession = Depends(get_db)) -> UpdateProduct:
    return UpdateProduct(repository=SQLAlchemyProductRepository(session))


def _delete_use_case(session: AsyncSession = Depends(get_db)) -> DeleteProduct:
    return DeleteProduct(repository=SQLAlchemyProductRepository(session))


def _to_item(product: Product) -> ProductItem:
    return ProductItem(
        id=product.id,
        slug=str(product.slug),
        name=product.name,
        short_description=product.short_description,
        full_description=product.full_description,
        status=product.status.value,
        url=str(product.url) if product.url else None,
        logo=str(product.logo) if product.logo else None,
        featured=product.featured,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def _to_input(payload: ProductWrite) -> ProductInput:
    return ProductInput(
        slug=payload.slug,
        name=payload.name,
        short_description=payload.short_description,
        full_description=payload.full_description,
        status=payload.status,
        url=payload.url,
        logo=payload.logo,
        featured=payload.featured,
    )


@public_router.get("", dependencies=[_public_api_limit])
async def list_products(
    use_case: ListProducts = Depends(_list_use_case),
) -> SuccessResponse[list[ProductItem]]:
    products = await use_case.execute()
    return SuccessResponse(data=[_to_item(p) for p in products])


@public_router.get("/{slug}", dependencies=[_public_api_limit])
async def get_product(
    slug: str, use_case: GetProductBySlug = Depends(_get_by_slug_use_case)
) -> SuccessResponse[ProductItem]:
    product = await use_case.execute(slug)
    return SuccessResponse(data=_to_item(product))


@admin_router.post("", status_code=201, dependencies=[_admin_write_limit])
async def create_product(
    payload: ProductWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: CreateProduct = Depends(_create_use_case),
) -> SuccessResponse[ProductItem]:
    product = await use_case.execute(_to_input(payload))
    return SuccessResponse(data=_to_item(product))


@admin_router.put("/{product_id}", dependencies=[_admin_write_limit])
async def update_product(
    product_id: uuid.UUID,
    payload: ProductWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: UpdateProduct = Depends(_update_use_case),
) -> SuccessResponse[ProductItem]:
    product = await use_case.execute(product_id, _to_input(payload))
    return SuccessResponse(data=_to_item(product))


@admin_router.delete(
    "/{product_id}", status_code=204, dependencies=[_admin_write_limit]
)
async def delete_product(
    product_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: DeleteProduct = Depends(_delete_use_case),
) -> None:
    await use_case.execute(product_id)
