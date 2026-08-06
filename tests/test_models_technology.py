import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.technology import Technology


async def test_technology_can_be_created(db_session: AsyncSession) -> None:
    tech = Technology(name="Python", category="Language")
    db_session.add(tech)
    await db_session.commit()

    assert tech.icon is None
    assert tech.official_url is None


async def test_technology_name_must_be_unique(db_session: AsyncSession) -> None:
    db_session.add(Technology(name="Duplicate", category="Language"))
    await db_session.commit()

    db_session.add(Technology(name="Duplicate", category="Other"))
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_project_technology_many_to_many_relationship(
    db_session: AsyncSession,
) -> None:
    project = Project(slug="ch-tech", title="CH-TECH")
    python = Technology(name="Python", category="Language")
    docker = Technology(name="Docker", category="Infra")
    project.technologies = [python, docker]

    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project, attribute_names=["technologies"])
    await db_session.refresh(python, attribute_names=["projects"])

    assert {t.name for t in project.technologies} == {"Python", "Docker"}
    assert project in python.projects
