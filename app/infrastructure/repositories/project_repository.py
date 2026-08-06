"""SQLAlchemy adapter for the ProjectRepository port (ADR-0012).

Fase 3 pilot: mirrors the query logic that used to live directly in
api/v1/projects.py, translated into the ProjectRepository Protocol so the
router can depend on app.application instead of SQLAlchemy directly.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.ports.project_repository import (
    ProjectFilters,
    ProjectInput,
    ProjectWithTechnologies,
)
from app.core.errors import ConflictError
from app.domain.enums import ProjectStatus, Visibility
from app.domain.project import Project as ProjectEntity
from app.domain.technology import Technology as TechnologyEntity
from app.domain.value_objects import Image, Slug, Url
from app.models import Project as ProjectModel
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


def _to_row(model: ProjectModel) -> ProjectWithTechnologies:
    project = ProjectEntity(
        id=model.id,
        slug=Slug(model.slug),
        title=model.title,
        short_description=model.short_description,
        full_description=model.full_description,
        repository_url=Url(model.repository_url) if model.repository_url else None,
        live_demo_url=Url(model.live_demo_url) if model.live_demo_url else None,
        cover_image=Image(model.cover_image) if model.cover_image else None,
        status=ProjectStatus(model.status),
        visibility=Visibility(model.visibility),
        featured=model.featured,
        client_id=model.client_id,
        started_at=model.started_at,
        finished_at=model.finished_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
    technologies = [_to_technology_entity(t) for t in model.technologies]
    return ProjectWithTechnologies(project=project, technologies=technologies)


class SQLAlchemyProjectRepository:
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
        self, filters: ProjectFilters, *, public_only: bool
    ) -> list[ProjectWithTechnologies]:
        query = select(ProjectModel).options(selectinload(ProjectModel.technologies))
        if public_only:
            query = query.where(ProjectModel.visibility == "PUBLIC")
        if filters.technology is not None:
            query = query.join(ProjectModel.technologies).where(
                TechnologyModel.name == filters.technology
            )
        if filters.featured is not None:
            query = query.where(ProjectModel.featured == filters.featured)
        if filters.status is not None:
            query = query.where(ProjectModel.status == filters.status)
        if filters.search is not None:
            # .ilike() has no native MySQL operator (unlike Postgres ILIKE) —
            # SQLAlchemy compiles it generically as LOWER(title) LIKE
            # LOWER(:term) on backends without one, so this call is unchanged.
            # Backed by a plain B-tree index on title (see models/project.py)
            # replacing the dropped pg_trgm/GIN trigram index — this catalog
            # is small enough that a full LIKE scan needs no fuzzy matching.
            query = query.where(ProjectModel.title.ilike(f"%{filters.search}%"))

        sort_column = (
            ProjectModel.title if filters.sort == "title" else ProjectModel.created_at
        )
        query = (
            query.order_by(sort_column)
            .offset((filters.page - 1) * filters.limit)
            .limit(filters.limit)
        )

        result = await self._session.execute(query)
        return [_to_row(model) for model in result.scalars().unique().all()]

    async def get_by_slug(
        self, slug: str, *, public_only: bool
    ) -> ProjectWithTechnologies | None:
        query = (
            select(ProjectModel)
            .options(selectinload(ProjectModel.technologies))
            .where(ProjectModel.slug == slug)
        )
        if public_only:
            query = query.where(ProjectModel.visibility == "PUBLIC")

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return _to_row(model) if model is not None else None

    async def get_by_id(self, project_id: uuid.UUID) -> ProjectWithTechnologies | None:
        result = await self._session.execute(
            select(ProjectModel)
            .options(selectinload(ProjectModel.technologies))
            .where(ProjectModel.id == project_id)
        )
        model = result.scalar_one_or_none()
        return _to_row(model) if model is not None else None

    async def create(self, data: ProjectInput) -> ProjectWithTechnologies:
        technologies = await self._get_technologies(data.technology_ids)
        model = ProjectModel(
            slug=data.slug,
            title=data.title,
            short_description=data.short_description,
            full_description=data.full_description,
            repository_url=data.repository_url,
            live_demo_url=data.live_demo_url,
            cover_image=data.cover_image,
            status=data.status.value,
            visibility=data.visibility.value,
            featured=data.featured,
            started_at=data.started_at,
            finished_at=data.finished_at,
            technologies=technologies,
        )
        self._session.add(model)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            raise ConflictError("A project with this slug already exists") from exc

        await self._session.refresh(model, attribute_names=["technologies"])
        return _to_row(model)

    async def update(
        self, project_id: uuid.UUID, data: ProjectInput
    ) -> ProjectWithTechnologies | None:
        result = await self._session.execute(
            select(ProjectModel)
            .options(selectinload(ProjectModel.technologies))
            .where(ProjectModel.id == project_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        model.slug = data.slug
        model.title = data.title
        model.short_description = data.short_description
        model.full_description = data.full_description
        model.repository_url = data.repository_url
        model.live_demo_url = data.live_demo_url
        model.cover_image = data.cover_image
        model.status = data.status.value
        model.visibility = data.visibility.value
        model.featured = data.featured
        model.started_at = data.started_at
        model.finished_at = data.finished_at
        # technologies was eager-loaded above — assigning it without that
        # would trigger an implicit lazy load, which async SQLAlchemy can't
        # do outside of an explicit greenlet context (raises MissingGreenlet).
        model.technologies = await self._get_technologies(data.technology_ids)

        try:
            await self._session.commit()
        except IntegrityError as exc:
            raise ConflictError("A project with this slug already exists") from exc

        await self._session.refresh(model, attribute_names=["technologies"])
        return _to_row(model)

    async def delete(self, project_id: uuid.UUID) -> bool:
        # Eager-load technologies: SQLAlchemy needs the current M2M
        # collection to clean up project_technologies rows on delete, and
        # async ORM can't do that via an implicit lazy load (MissingGreenlet).
        result = await self._session.execute(
            select(ProjectModel)
            .options(selectinload(ProjectModel.technologies))
            .where(ProjectModel.id == project_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            raise ConflictError(
                "Project is referenced by an existing case study or testimonial"
            ) from exc
        return True
