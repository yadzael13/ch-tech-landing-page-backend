"""SQLAlchemy adapter for the TestimonialRepository port (ADR-0012, Fase 6)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.testimonial_repository import TestimonialInput
from app.domain.testimonial import Testimonial as TestimonialEntity
from app.models import Testimonial as TestimonialModel


def _to_entity(model: TestimonialModel) -> TestimonialEntity:
    return TestimonialEntity(
        id=model.id,
        author_name=model.author_name,
        author_role=model.author_role,
        client_id=model.client_id,
        project_id=model.project_id,
        content=model.content,
        rating=model.rating,
        featured=model.featured,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyTestimonialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[TestimonialEntity]:
        result = await self._session.execute(
            select(TestimonialModel).order_by(TestimonialModel.created_at)
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def create(self, data: TestimonialInput) -> TestimonialEntity:
        model = TestimonialModel(
            author_name=data.author_name,
            author_role=data.author_role,
            client_id=data.client_id,
            project_id=data.project_id,
            content=data.content,
            rating=data.rating,
            featured=data.featured,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(
        self, testimonial_id: uuid.UUID, data: TestimonialInput
    ) -> TestimonialEntity | None:
        result = await self._session.execute(
            select(TestimonialModel).where(TestimonialModel.id == testimonial_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        model.author_name = data.author_name
        model.author_role = data.author_role
        model.client_id = data.client_id
        model.project_id = data.project_id
        model.content = data.content
        model.rating = data.rating
        model.featured = data.featured

        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, testimonial_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(TestimonialModel).where(TestimonialModel.id == testimonial_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.commit()
        return True
