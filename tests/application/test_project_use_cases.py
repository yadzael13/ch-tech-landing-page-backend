import uuid
from datetime import UTC, datetime

import pytest

from app.application.ports.project_repository import (
    ProjectFilters,
    ProjectInput,
    ProjectWithTechnologies,
)
from app.application.use_cases.projects import (
    CreateProject,
    DeleteProject,
    GetProjectById,
    GetProjectBySlug,
    ListProjects,
    UpdateProject,
)
from app.core.errors import ResourceNotFoundError
from app.domain.enums import ProjectStatus, Visibility
from app.domain.project import Project
from app.domain.value_objects import Slug
from tests.application.fakes import InMemoryProjectRepository


def _project(**overrides: object) -> ProjectWithTechnologies:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "slug": Slug("sample"),
        "title": "Sample",
        "short_description": None,
        "full_description": None,
        "repository_url": None,
        "live_demo_url": None,
        "cover_image": None,
        "status": ProjectStatus.PLANNING,
        "visibility": Visibility.PUBLIC,
        "featured": False,
        "client_id": None,
        "started_at": None,
        "finished_at": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return ProjectWithTechnologies(project=Project(**defaults), technologies=[])  # type: ignore[arg-type]


def _input(**overrides: object) -> ProjectInput:
    defaults: dict[str, object] = {
        "slug": "new-project",
        "title": "New Project",
        "short_description": None,
        "full_description": None,
        "status": ProjectStatus.PLANNING,
        "visibility": Visibility.PRIVATE,
        "featured": False,
        "started_at": None,
        "finished_at": None,
        "technology_ids": [],
    }
    defaults.update(overrides)
    return ProjectInput(**defaults)  # type: ignore[arg-type]


async def test_list_projects_delegates_to_the_repository() -> None:
    public = _project(visibility=Visibility.PUBLIC)
    private = _project(visibility=Visibility.PRIVATE)
    repo = InMemoryProjectRepository([public, private])
    use_case = ListProjects(repository=repo)

    result = await use_case.execute(ProjectFilters(), public_only=True)

    assert [r.project.id for r in result] == [public.project.id]


async def test_get_project_by_slug_raises_not_found_when_missing() -> None:
    use_case = GetProjectBySlug(repository=InMemoryProjectRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute("does-not-exist", public_only=True)


async def test_get_project_by_slug_returns_the_match() -> None:
    row = _project(slug=Slug("found-me"))
    use_case = GetProjectBySlug(repository=InMemoryProjectRepository([row]))

    result = await use_case.execute("found-me", public_only=True)

    assert result.project.id == row.project.id


async def test_get_project_by_id_raises_not_found_when_missing() -> None:
    use_case = GetProjectById(repository=InMemoryProjectRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_create_project_persists_through_the_repository() -> None:
    repo = InMemoryProjectRepository()
    use_case = CreateProject(repository=repo)

    result = await use_case.execute(_input(slug="brand-new", title="Brand New"))

    assert str(result.project.slug) == "brand-new"
    assert await repo.get_by_id(result.project.id) is not None


async def test_create_project_rejects_a_duplicate_slug() -> None:
    repo = InMemoryProjectRepository([_project(slug=Slug("taken"))])
    use_case = CreateProject(repository=repo)

    from app.core.errors import ConflictError

    with pytest.raises(ConflictError):
        await use_case.execute(_input(slug="taken"))


async def test_update_project_raises_not_found_when_missing() -> None:
    use_case = UpdateProject(repository=InMemoryProjectRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4(), _input())


async def test_update_project_applies_changes() -> None:
    row = _project(title="Old Title")
    repo = InMemoryProjectRepository([row])
    use_case = UpdateProject(repository=repo)

    result = await use_case.execute(
        row.project.id, _input(slug=str(row.project.slug), title="New Title")
    )

    assert result.project.title == "New Title"


async def test_delete_project_raises_not_found_when_missing() -> None:
    use_case = DeleteProject(repository=InMemoryProjectRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_delete_project_removes_it() -> None:
    row = _project()
    repo = InMemoryProjectRepository([row])
    use_case = DeleteProject(repository=repo)

    await use_case.execute(row.project.id)

    assert await repo.get_by_id(row.project.id) is None
