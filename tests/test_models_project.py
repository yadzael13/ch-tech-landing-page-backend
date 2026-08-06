import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus, Visibility


async def test_project_defaults(db_session: AsyncSession) -> None:
    project = Project(slug="ch-tech", title="CH-TECH")
    db_session.add(project)
    await db_session.commit()

    assert project.status == ProjectStatus.PLANNING.value
    assert project.visibility == Visibility.PRIVATE.value
    assert project.featured is False


async def test_project_requires_a_title(db_session: AsyncSession) -> None:
    db_session.add(Project(slug="no-title", title=None))
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_project_slug_must_be_unique(db_session: AsyncSession) -> None:
    db_session.add(Project(slug="dup", title="First"))
    await db_session.commit()

    db_session.add(Project(slug="dup", title="Second"))
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_project_rejects_invalid_status(db_session: AsyncSession) -> None:
    db_session.add(Project(slug="bad-status", title="Bad", status="NOT_A_STATUS"))
    # MySQL raises CHECK constraint violations as OperationalError (error
    # 3819), not IntegrityError like Postgres.
    with pytest.raises(OperationalError):
        await db_session.commit()


async def test_project_rejects_invalid_visibility(db_session: AsyncSession) -> None:
    db_session.add(
        Project(slug="bad-visibility", title="Bad", visibility="NOT_A_VISIBILITY")
    )
    with pytest.raises(OperationalError):
        await db_session.commit()
