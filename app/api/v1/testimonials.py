import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.application.ports.testimonial_repository import TestimonialInput
from app.application.use_cases.testimonials import (
    CreateTestimonial,
    DeleteTestimonial,
    ListTestimonials,
    UpdateTestimonial,
)
from app.core.rate_limit import ip_rate_limiter
from app.db.session import get_db
from app.domain.testimonial import Testimonial
from app.infrastructure.repositories.client_repository import (
    SQLAlchemyClientRepository,
)
from app.infrastructure.repositories.project_repository import (
    SQLAlchemyProjectRepository,
)
from app.infrastructure.repositories.testimonial_repository import (
    SQLAlchemyTestimonialRepository,
)
from app.schemas.response import SuccessResponse
from app.schemas.testimonial import TestimonialItem, TestimonialWrite

public_router = APIRouter(prefix="/testimonials", tags=["testimonials"])
admin_router = APIRouter(prefix="/admin/testimonials", tags=["admin:testimonials"])

# API.md "Rate Limiting" -> "API Pública": 100 requests/minute/IP.
_public_api_limit = Depends(
    ip_rate_limiter(limit=100, window_seconds=60, scope="public-api")
)

# Admin writes are auth-gated but otherwise had no throttle — a leaked
# access token could hammer these without limit (OWASP API4:2023).
_admin_write_limit = Depends(
    ip_rate_limiter(limit=60, window_seconds=60, scope="admin-write")
)


def _list_use_case(session: AsyncSession = Depends(get_db)) -> ListTestimonials:
    return ListTestimonials(repository=SQLAlchemyTestimonialRepository(session))


def _create_use_case(session: AsyncSession = Depends(get_db)) -> CreateTestimonial:
    return CreateTestimonial(
        repository=SQLAlchemyTestimonialRepository(session),
        client_repository=SQLAlchemyClientRepository(session),
        project_repository=SQLAlchemyProjectRepository(session),
    )


def _update_use_case(session: AsyncSession = Depends(get_db)) -> UpdateTestimonial:
    return UpdateTestimonial(
        repository=SQLAlchemyTestimonialRepository(session),
        client_repository=SQLAlchemyClientRepository(session),
        project_repository=SQLAlchemyProjectRepository(session),
    )


def _delete_use_case(session: AsyncSession = Depends(get_db)) -> DeleteTestimonial:
    return DeleteTestimonial(repository=SQLAlchemyTestimonialRepository(session))


def _to_item(testimonial: Testimonial) -> TestimonialItem:
    return TestimonialItem(
        id=testimonial.id,
        author_name=testimonial.author_name,
        author_role=testimonial.author_role,
        client_id=testimonial.client_id,
        project_id=testimonial.project_id,
        content=testimonial.content,
        rating=testimonial.rating,
        featured=testimonial.featured,
        created_at=testimonial.created_at,
        updated_at=testimonial.updated_at,
    )


def _to_input(payload: TestimonialWrite) -> TestimonialInput:
    return TestimonialInput(
        author_name=payload.author_name,
        author_role=payload.author_role,
        client_id=payload.client_id,
        project_id=payload.project_id,
        content=payload.content,
        rating=payload.rating,
        featured=payload.featured,
    )


@public_router.get("", dependencies=[_public_api_limit])
async def list_testimonials(
    use_case: ListTestimonials = Depends(_list_use_case),
) -> SuccessResponse[list[TestimonialItem]]:
    testimonials = await use_case.execute()
    return SuccessResponse(data=[_to_item(t) for t in testimonials])


@admin_router.post("", status_code=201, dependencies=[_admin_write_limit])
async def create_testimonial(
    payload: TestimonialWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: CreateTestimonial = Depends(_create_use_case),
) -> SuccessResponse[TestimonialItem]:
    testimonial = await use_case.execute(_to_input(payload))
    return SuccessResponse(data=_to_item(testimonial))


@admin_router.put("/{testimonial_id}", dependencies=[_admin_write_limit])
async def update_testimonial(
    testimonial_id: uuid.UUID,
    payload: TestimonialWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: UpdateTestimonial = Depends(_update_use_case),
) -> SuccessResponse[TestimonialItem]:
    testimonial = await use_case.execute(testimonial_id, _to_input(payload))
    return SuccessResponse(data=_to_item(testimonial))


@admin_router.delete(
    "/{testimonial_id}", status_code=204, dependencies=[_admin_write_limit]
)
async def delete_testimonial(
    testimonial_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: DeleteTestimonial = Depends(_delete_use_case),
) -> None:
    await use_case.execute(testimonial_id)
