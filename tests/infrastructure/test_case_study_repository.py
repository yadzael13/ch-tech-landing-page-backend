import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.case_study_repository import CaseStudyInput
from app.infrastructure.repositories.case_study_repository import (
    SQLAlchemyCaseStudyRepository,
)
from app.models import Project as ProjectModel


async def _make_project(
    db_session: AsyncSession, *, visibility: str = "PUBLIC"
) -> uuid.UUID:
    project = ProjectModel(
        slug=f"project-{uuid.uuid4()}", title="Project", visibility=visibility
    )
    db_session.add(project)
    await db_session.flush()
    return project.id


def _input(project_id: uuid.UUID, **overrides: object) -> CaseStudyInput:
    defaults: dict[str, object] = {
        "project_id": project_id,
        "challenge": "Scale",
        "solution": "Clean Architecture",
        "architecture": None,
        "lessons_learned": None,
        "metrics": None,
    }
    defaults.update(overrides)
    return CaseStudyInput(**defaults)  # type: ignore[arg-type]


async def test_create_persists_and_returns_the_case_study(
    db_session: AsyncSession,
) -> None:
    project_id = await _make_project(db_session)
    repo = SQLAlchemyCaseStudyRepository(db_session)

    result = await repo.create(_input(project_id))

    assert result.project_id == project_id
    assert result.challenge == "Scale"


async def test_list_hides_case_studies_of_private_projects_when_public_only(
    db_session: AsyncSession,
) -> None:
    public_project_id = await _make_project(db_session, visibility="PUBLIC")
    private_project_id = await _make_project(db_session, visibility="PRIVATE")
    repo = SQLAlchemyCaseStudyRepository(db_session)
    await repo.create(_input(public_project_id))
    await repo.create(_input(private_project_id))

    result = await repo.list(public_only=True)

    assert [c.project_id for c in result] == [public_project_id]


async def test_get_by_id_hides_private_project_case_study_when_public_only(
    db_session: AsyncSession,
) -> None:
    private_project_id = await _make_project(db_session, visibility="PRIVATE")
    repo = SQLAlchemyCaseStudyRepository(db_session)
    created = await repo.create(_input(private_project_id))

    assert await repo.get_by_id(created.id, public_only=True) is None
    found = await repo.get_by_id(created.id, public_only=False)
    assert found is not None


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyCaseStudyRepository(db_session)
    assert await repo.get_by_id(uuid.uuid4(), public_only=False) is None


async def test_update_returns_none_when_missing(db_session: AsyncSession) -> None:
    project_id = await _make_project(db_session)
    repo = SQLAlchemyCaseStudyRepository(db_session)
    assert await repo.update(uuid.uuid4(), _input(project_id)) is None


async def test_update_applies_changes(db_session: AsyncSession) -> None:
    project_id = await _make_project(db_session)
    repo = SQLAlchemyCaseStudyRepository(db_session)
    created = await repo.create(_input(project_id, challenge="Old"))

    updated = await repo.update(created.id, _input(project_id, challenge="New"))

    assert updated is not None
    assert updated.challenge == "New"


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyCaseStudyRepository(db_session)
    assert await repo.delete(uuid.uuid4()) is False


async def test_delete_removes_the_case_study(db_session: AsyncSession) -> None:
    project_id = await _make_project(db_session)
    repo = SQLAlchemyCaseStudyRepository(db_session)
    created = await repo.create(_input(project_id))

    assert await repo.delete(created.id) is True
    assert await repo.get_by_id(created.id, public_only=False) is None


async def test_round_trip_preserves_metrics(db_session: AsyncSession) -> None:
    project_id = await _make_project(db_session)
    repo = SQLAlchemyCaseStudyRepository(db_session)
    created = await repo.create(
        _input(project_id, metrics={"loc": 1200, "coverage": 0.93})
    )

    fetched = await repo.get_by_id(created.id, public_only=False)

    assert fetched is not None
    assert fetched.metrics == {"loc": 1200, "coverage": 0.93}
