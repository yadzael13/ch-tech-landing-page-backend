"""SQLAlchemy adapter for the CaseStudyRepository port (ADR-0012, Fase 4)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.case_study_repository import CaseStudyInput
from app.domain.case_study import CaseStudy as CaseStudyEntity
from app.models import CaseStudy as CaseStudyModel
from app.models import Project as ProjectModel


def _to_entity(model: CaseStudyModel) -> CaseStudyEntity:
    return CaseStudyEntity(
        id=model.id,
        project_id=model.project_id,
        challenge=model.challenge,
        solution=model.solution,
        architecture=model.architecture,
        lessons_learned=model.lessons_learned,
        metrics=model.metrics,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyCaseStudyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, *, public_only: bool) -> list[CaseStudyEntity]:
        query = select(CaseStudyModel).order_by(CaseStudyModel.created_at)
        if public_only:
            query = query.join(
                ProjectModel, CaseStudyModel.project_id == ProjectModel.id
            ).where(ProjectModel.visibility == "PUBLIC")

        result = await self._session.execute(query)
        return [_to_entity(model) for model in result.scalars().all()]

    async def get_by_id(
        self, case_study_id: uuid.UUID, *, public_only: bool
    ) -> CaseStudyEntity | None:
        query = select(CaseStudyModel).where(CaseStudyModel.id == case_study_id)
        if public_only:
            query = query.join(
                ProjectModel, CaseStudyModel.project_id == ProjectModel.id
            ).where(ProjectModel.visibility == "PUBLIC")

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def create(self, data: CaseStudyInput) -> CaseStudyEntity:
        model = CaseStudyModel(
            project_id=data.project_id,
            challenge=data.challenge,
            solution=data.solution,
            architecture=data.architecture,
            lessons_learned=data.lessons_learned,
            metrics=data.metrics,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(
        self, case_study_id: uuid.UUID, data: CaseStudyInput
    ) -> CaseStudyEntity | None:
        result = await self._session.execute(
            select(CaseStudyModel).where(CaseStudyModel.id == case_study_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        model.project_id = data.project_id
        model.challenge = data.challenge
        model.solution = data.solution
        model.architecture = data.architecture
        model.lessons_learned = data.lessons_learned
        model.metrics = data.metrics

        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, case_study_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(CaseStudyModel).where(CaseStudyModel.id == case_study_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.commit()
        return True
