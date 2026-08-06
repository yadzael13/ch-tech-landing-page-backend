import uuid
from datetime import UTC, datetime

import pytest

from app.application.ports.case_study_repository import CaseStudyInput
from app.application.ports.project_repository import ProjectInput
from app.application.use_cases.case_studies import (
    CreateCaseStudy,
    DeleteCaseStudy,
    GetCaseStudyById,
    ListCaseStudies,
    UpdateCaseStudy,
)
from app.core.errors import ResourceNotFoundError
from app.domain.case_study import CaseStudy
from app.domain.enums import ProjectStatus, Visibility
from app.domain.project import Project
from app.domain.value_objects import Slug
from tests.application.fakes import (
    InMemoryCaseStudyRepository,
    InMemoryProjectRepository,
)


def _project(**overrides: object) -> Project:
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
        "status": ProjectStatus.COMPLETED,
        "visibility": Visibility.PUBLIC,
        "featured": False,
        "client_id": None,
        "started_at": None,
        "finished_at": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Project(**defaults)  # type: ignore[arg-type]


def _case_study(**overrides: object) -> CaseStudy:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "project_id": uuid.uuid4(),
        "challenge": None,
        "solution": None,
        "architecture": None,
        "lessons_learned": None,
        "metrics": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return CaseStudy(**defaults)  # type: ignore[arg-type]


def _input(**overrides: object) -> CaseStudyInput:
    defaults: dict[str, object] = {
        "project_id": uuid.uuid4(),
        "challenge": "Scale",
        "solution": "Clean Architecture",
        "architecture": None,
        "lessons_learned": None,
        "metrics": None,
    }
    defaults.update(overrides)
    return CaseStudyInput(**defaults)  # type: ignore[arg-type]


async def test_list_case_studies_hides_private_projects_when_public_only() -> None:
    public_project = _project()
    private_project = _project(visibility=Visibility.PRIVATE)
    public_case_study = _case_study(project_id=public_project.id)
    private_case_study = _case_study(project_id=private_project.id)
    repo = InMemoryCaseStudyRepository(
        [public_case_study, private_case_study],
        public_project_ids={public_project.id},
    )
    use_case = ListCaseStudies(repository=repo)

    result = await use_case.execute(public_only=True)

    assert [c.id for c in result] == [public_case_study.id]


async def test_get_case_study_by_id_raises_not_found_when_missing() -> None:
    use_case = GetCaseStudyById(repository=InMemoryCaseStudyRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4(), public_only=True)


async def test_create_case_study_requires_an_existing_project() -> None:
    use_case = CreateCaseStudy(
        repository=InMemoryCaseStudyRepository(),
        project_repository=InMemoryProjectRepository(),
    )

    with pytest.raises(ResourceNotFoundError, match="Project not found"):
        await use_case.execute(_input(project_id=uuid.uuid4()))


async def test_create_case_study_succeeds_for_an_existing_project() -> None:
    project_repository = InMemoryProjectRepository()
    created_project = await project_repository.create(
        ProjectInput(
            slug="sample",
            title="Sample",
            short_description=None,
            full_description=None,
            status=ProjectStatus.COMPLETED,
            visibility=Visibility.PUBLIC,
            featured=False,
            started_at=None,
            finished_at=None,
        )
    )
    use_case = CreateCaseStudy(
        repository=InMemoryCaseStudyRepository(),
        project_repository=project_repository,
    )

    result = await use_case.execute(_input(project_id=created_project.project.id))

    assert result.project_id == created_project.project.id


async def test_update_case_study_raises_not_found_when_case_study_missing() -> None:
    use_case = UpdateCaseStudy(
        repository=InMemoryCaseStudyRepository(),
        project_repository=InMemoryProjectRepository(),
    )

    with pytest.raises(ResourceNotFoundError, match="Case study not found"):
        await use_case.execute(uuid.uuid4(), _input())


async def test_delete_case_study_raises_not_found_when_missing() -> None:
    use_case = DeleteCaseStudy(repository=InMemoryCaseStudyRepository())

    with pytest.raises(ResourceNotFoundError):
        await use_case.execute(uuid.uuid4())


async def test_delete_case_study_removes_it() -> None:
    case_study = _case_study()
    repo = InMemoryCaseStudyRepository([case_study])
    use_case = DeleteCaseStudy(repository=repo)

    await use_case.execute(case_study.id)

    assert await repo.get_by_id(case_study.id, public_only=False) is None
