import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_study import CaseStudy
from app.models.project import Project


async def _create_project(db_session: AsyncSession) -> Project:
    project = Project(slug="ch-tech", title="CH-TECH")
    db_session.add(project)
    await db_session.flush()
    return project


async def test_case_study_belongs_to_a_project(db_session: AsyncSession) -> None:
    project = await _create_project(db_session)
    case_study = CaseStudy(
        project_id=project.id,
        challenge="Scale to 10k users",
        solution="Caching + read replicas",
        metrics={"latency_ms": 42},
    )
    db_session.add(case_study)
    await db_session.commit()

    assert case_study.project_id == project.id
    assert case_study.metrics == {"latency_ms": 42}


async def test_case_study_requires_an_existing_project(
    db_session: AsyncSession,
) -> None:
    db_session.add(CaseStudy(project_id=uuid.uuid4(), challenge="orphan"))
    with pytest.raises(IntegrityError):
        await db_session.commit()
