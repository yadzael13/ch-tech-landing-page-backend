import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.project_repository import ProjectFilters, ProjectInput
from app.core.errors import ConflictError
from app.domain.enums import ProjectStatus, Visibility
from app.infrastructure.repositories.project_repository import (
    SQLAlchemyProjectRepository,
)
from app.models import CaseStudy as CaseStudyModel
from app.models import Technology as TechnologyModel


def _input(**overrides: object) -> ProjectInput:
    defaults: dict[str, object] = {
        "slug": "repo-test",
        "title": "Repo Test",
        "short_description": None,
        "full_description": None,
        "status": ProjectStatus.PLANNING,
        "visibility": Visibility.PUBLIC,
        "featured": False,
        "started_at": None,
        "finished_at": None,
        "technology_ids": [],
    }
    defaults.update(overrides)
    return ProjectInput(**defaults)  # type: ignore[arg-type]


async def test_create_persists_and_returns_the_project(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyProjectRepository(db_session)

    result = await repo.create(_input(slug="brand-new", title="Brand New"))

    assert str(result.project.slug) == "brand-new"
    assert result.project.id is not None


async def test_create_rejects_a_duplicate_slug(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProjectRepository(db_session)
    await repo.create(_input(slug="taken"))

    with pytest.raises(ConflictError):
        await repo.create(_input(slug="taken"))


async def test_create_attaches_the_requested_technologies(
    db_session: AsyncSession,
) -> None:
    tech = TechnologyModel(name="Python", category="Language")
    db_session.add(tech)
    await db_session.flush()

    repo = SQLAlchemyProjectRepository(db_session)
    result = await repo.create(_input(slug="with-tech", technology_ids=[tech.id]))

    assert [t.name for t in result.technologies] == ["Python"]


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProjectRepository(db_session)
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_get_by_slug_hides_private_projects_when_public_only(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyProjectRepository(db_session)
    await repo.create(_input(slug="private-one", visibility=Visibility.PRIVATE))

    assert await repo.get_by_slug("private-one", public_only=True) is None
    found = await repo.get_by_slug("private-one", public_only=False)
    assert found is not None
    assert str(found.project.slug) == "private-one"


async def test_list_filters_by_featured(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProjectRepository(db_session)
    await repo.create(_input(slug="featured-one", featured=True))
    await repo.create(_input(slug="not-featured", featured=False))

    result = await repo.list(ProjectFilters(featured=True), public_only=True)

    assert [str(r.project.slug) for r in result] == ["featured-one"]


async def test_update_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProjectRepository(db_session)
    result = await repo.update(uuid.uuid4(), _input())
    assert result is None


async def test_update_applies_changes(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProjectRepository(db_session)
    created = await repo.create(_input(slug="to-update", title="Old Title"))

    updated = await repo.update(
        created.project.id, _input(slug="to-update", title="New Title")
    )

    assert updated is not None
    assert updated.project.title == "New Title"


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProjectRepository(db_session)
    assert await repo.delete(uuid.uuid4()) is False


async def test_delete_removes_the_project(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProjectRepository(db_session)
    created = await repo.create(_input(slug="to-delete"))

    assert await repo.delete(created.project.id) is True
    assert await repo.get_by_id(created.project.id) is None


async def test_delete_with_technologies_cleans_up_the_relation(
    db_session: AsyncSession,
) -> None:
    tech = TechnologyModel(name="Docker", category="Infra")
    db_session.add(tech)
    await db_session.flush()

    repo = SQLAlchemyProjectRepository(db_session)
    created = await repo.create(
        _input(slug="to-delete-with-tech", technology_ids=[tech.id])
    )

    assert await repo.delete(created.project.id) is True


async def test_delete_raises_conflict_when_referenced_by_a_case_study(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyProjectRepository(db_session)
    created = await repo.create(_input(slug="has-case-study"))

    db_session.add(CaseStudyModel(project_id=created.project.id))
    await db_session.commit()

    with pytest.raises(ConflictError):
        await repo.delete(created.project.id)


async def test_round_trip_preserves_urls(db_session: AsyncSession) -> None:
    repo = SQLAlchemyProjectRepository(db_session)
    created = await repo.create(
        _input(
            slug="with-urls",
            repository_url="https://github.com/ch-tech/ch-tech",
            cover_image="https://ch-tech.dev/cover.png",
        )
    )

    fetched = await repo.get_by_id(created.project.id)

    assert fetched is not None
    assert str(fetched.project.repository_url) == "https://github.com/ch-tech/ch-tech"
    assert str(fetched.project.cover_image) == "https://ch-tech.dev/cover.png"
