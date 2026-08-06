import uuid
from datetime import UTC, datetime

from app.domain.enums import ProjectStatus, Visibility
from app.domain.project import Project
from app.domain.value_objects import Image, Slug, Url


def _project(**overrides: object) -> Project:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "slug": Slug("ch-tech-v2"),
        "title": "CH-TECH V2",
        "short_description": None,
        "full_description": None,
        "repository_url": None,
        "live_demo_url": None,
        "cover_image": None,
        "status": ProjectStatus.IN_PROGRESS,
        "visibility": Visibility.PUBLIC,
        "featured": True,
        "client_id": None,
        "started_at": None,
        "finished_at": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Project(**defaults)  # type: ignore[arg-type]


def test_project_holds_a_slug_value_object() -> None:
    assert str(_project().slug) == "ch-tech-v2"


def test_project_urls_are_value_objects_when_present() -> None:
    project = _project(
        repository_url=Url("https://github.com/ch-tech/ch-tech"),
        cover_image=Image("https://ch-tech.dev/cover.png"),
    )
    assert isinstance(project.repository_url, Url)
    assert isinstance(project.cover_image, Image)


def test_project_own_work_has_no_client() -> None:
    assert _project(client_id=None).client_id is None


def test_project_for_a_client_references_it_by_id() -> None:
    client_id = uuid.uuid4()
    assert _project(client_id=client_id).client_id == client_id
