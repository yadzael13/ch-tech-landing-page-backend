import uuid

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.technology_repository import (
    TechnologyFilters,
    TechnologyInput,
)
from app.infrastructure.repositories.technology_repository import (
    SQLAlchemyTechnologyRepository,
)
from app.models import Project as ProjectModel
from app.models.associations import project_technologies


def _input(**overrides: object) -> TechnologyInput:
    defaults: dict[str, object] = {"name": "FastAPI", "category": "Backend"}
    defaults.update(overrides)
    return TechnologyInput(**defaults)  # type: ignore[arg-type]


async def test_create_persists_and_returns_the_technology(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyTechnologyRepository(db_session)

    result = await repo.create(_input(name="Redis"))

    assert result.name == "Redis"
    assert result.id is not None


async def test_list_filters_by_category(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTechnologyRepository(db_session)
    await repo.create(_input(name="FastAPI", category="Backend"))
    await repo.create(_input(name="Next.js", category="Frontend"))

    result = await repo.list(TechnologyFilters(category="Frontend"))

    assert [t.name for t in result] == ["Next.js"]


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTechnologyRepository(db_session)
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_update_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTechnologyRepository(db_session)
    assert await repo.update(uuid.uuid4(), _input()) is None


async def test_update_applies_changes(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTechnologyRepository(db_session)
    created = await repo.create(_input(name="Old Name"))

    updated = await repo.update(created.id, _input(name="New Name"))

    assert updated is not None
    assert updated.name == "New Name"


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTechnologyRepository(db_session)
    assert await repo.delete(uuid.uuid4()) is False


async def test_delete_removes_the_technology(db_session: AsyncSession) -> None:
    repo = SQLAlchemyTechnologyRepository(db_session)
    created = await repo.create(_input())

    assert await repo.delete(created.id) is True
    assert await repo.get_by_id(created.id) is None


async def test_delete_cleans_up_the_relation_when_referenced_by_a_project(
    db_session: AsyncSession,
) -> None:
    # Unlike a plain scalar FK (see client/project/service_line repository
    # tests), a many-to-many secondary table doesn't need the parent to
    # eager-load the collection first: SQLAlchemy's unit of work resolves
    # the project_technologies dependency for a bare session.delete(model)
    # on its own and removes the association row — no FK conflict to guard
    # against here, confirmed via the table-level insert below (which,
    # unlike assigning project.technologies, leaves the ORM with no
    # in-memory knowledge of the link beforehand).
    repo = SQLAlchemyTechnologyRepository(db_session)
    created = await repo.create(_input(name="In Use"))

    project = ProjectModel(slug="uses-tech", title="Uses Tech")
    db_session.add(project)
    await db_session.flush()
    await db_session.execute(
        insert(project_technologies).values(
            project_id=project.id, technology_id=created.id
        )
    )
    await db_session.commit()

    assert await repo.delete(created.id) is True

    remaining = await db_session.execute(select(project_technologies))
    assert remaining.all() == []


async def test_round_trip_preserves_icon_and_official_url(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyTechnologyRepository(db_session)
    created = await repo.create(
        _input(
            icon="https://ch-tech.dev/icons/fastapi.svg",
            official_url="https://fastapi.tiangolo.com",
        )
    )

    fetched = await repo.get_by_id(created.id)

    assert fetched is not None
    assert str(fetched.icon) == "https://ch-tech.dev/icons/fastapi.svg"
    assert str(fetched.official_url) == "https://fastapi.tiangolo.com"
