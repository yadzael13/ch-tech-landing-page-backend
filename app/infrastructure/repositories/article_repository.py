"""SQLAlchemy adapter for the ArticleRepository port (ADR-0012, Fase 4)."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.ports.article_repository import (
    ArticleInput,
    ArticleWithTechnologies,
)
from app.core.errors import ConflictError
from app.domain.article import Article as ArticleEntity
from app.domain.technology import Technology as TechnologyEntity
from app.domain.value_objects import Image, MarkdownContent, Slug, Url
from app.models import Article as ArticleModel
from app.models import Technology as TechnologyModel


def _to_technology_entity(model: TechnologyModel) -> TechnologyEntity:
    return TechnologyEntity(
        id=model.id,
        name=model.name,
        category=model.category,
        icon=Image(model.icon) if model.icon else None,
        official_url=Url(model.official_url) if model.official_url else None,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_row(model: ArticleModel) -> ArticleWithTechnologies:
    article = ArticleEntity(
        id=model.id,
        author_id=model.author_id,
        slug=Slug(model.slug),
        title=model.title,
        summary=model.summary,
        content=MarkdownContent(model.content),
        cover_image=Image(model.cover_image) if model.cover_image else None,
        reading_time=model.reading_time,
        published=model.published,
        published_at=model.published_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
    technologies = [_to_technology_entity(t) for t in model.technologies]
    return ArticleWithTechnologies(article=article, technologies=technologies)


class SQLAlchemyArticleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_technologies(
        self, technology_ids: list[uuid.UUID]
    ) -> list[TechnologyModel]:
        if not technology_ids:
            return []
        result = await self._session.execute(
            select(TechnologyModel).where(TechnologyModel.id.in_(technology_ids))
        )
        return list(result.scalars().all())

    async def list(
        self, *, published_only: bool, page: int, limit: int
    ) -> list[ArticleWithTechnologies]:
        query = select(ArticleModel).options(selectinload(ArticleModel.technologies))
        if published_only:
            query = query.where(ArticleModel.published.is_(True))
        query = (
            query.order_by(ArticleModel.published_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        result = await self._session.execute(query)
        return [_to_row(model) for model in result.scalars().unique().all()]

    async def get_by_slug(
        self, slug: str, *, published_only: bool
    ) -> ArticleWithTechnologies | None:
        query = (
            select(ArticleModel)
            .options(selectinload(ArticleModel.technologies))
            .where(ArticleModel.slug == slug)
        )
        if published_only:
            query = query.where(ArticleModel.published.is_(True))

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return _to_row(model) if model is not None else None

    async def get_by_id(self, article_id: uuid.UUID) -> ArticleWithTechnologies | None:
        result = await self._session.execute(
            select(ArticleModel)
            .options(selectinload(ArticleModel.technologies))
            .where(ArticleModel.id == article_id)
        )
        model = result.scalar_one_or_none()
        return _to_row(model) if model is not None else None

    async def create(
        self, data: ArticleInput, *, author_id: uuid.UUID
    ) -> ArticleWithTechnologies:
        technologies = await self._get_technologies(data.technology_ids)
        model = ArticleModel(
            author_id=author_id,
            slug=data.slug,
            title=data.title,
            summary=data.summary,
            content=data.content,
            cover_image=data.cover_image,
            reading_time=data.reading_time,
            published=data.published,
            published_at=data.published_at,
            technologies=technologies,
        )
        self._session.add(model)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            raise ConflictError("An article with this slug already exists") from exc

        await self._session.refresh(model, attribute_names=["technologies"])
        return _to_row(model)

    async def update(
        self, article_id: uuid.UUID, data: ArticleInput
    ) -> ArticleWithTechnologies | None:
        result = await self._session.execute(
            select(ArticleModel)
            .options(selectinload(ArticleModel.technologies))
            .where(ArticleModel.id == article_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        model.slug = data.slug
        model.title = data.title
        model.summary = data.summary
        model.content = data.content
        model.cover_image = data.cover_image
        model.reading_time = data.reading_time
        model.published = data.published
        model.published_at = data.published_at
        # technologies was eager-loaded above — assigning it without that
        # would trigger an implicit lazy load, which async SQLAlchemy can't
        # do outside of an explicit greenlet context (raises MissingGreenlet).
        model.technologies = await self._get_technologies(data.technology_ids)

        try:
            await self._session.commit()
        except IntegrityError as exc:
            raise ConflictError("An article with this slug already exists") from exc

        await self._session.refresh(model, attribute_names=["technologies"])
        return _to_row(model)

    async def delete(self, article_id: uuid.UUID) -> bool:
        # Eager-load technologies: SQLAlchemy needs the current M2M
        # collection to clean up article_technologies rows on delete, and
        # async ORM can't do that via an implicit lazy load (MissingGreenlet).
        result = await self._session.execute(
            select(ArticleModel)
            .options(selectinload(ArticleModel.technologies))
            .where(ArticleModel.id == article_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.commit()
        return True
