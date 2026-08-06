import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import CaseStudy, Project, User


async def _create_admin(db_session: AsyncSession) -> str:
    user = User(
        name="Admin",
        email=f"{uuid.uuid4()}@ch-tech.dev",
        password_hash=hash_password("s3cret-pass"),
    )
    db_session.add(user)
    await db_session.flush()
    return create_access_token(subject=str(user.id), role=user.role)


async def _create_project(db_session: AsyncSession, *, visibility: str) -> Project:
    project = Project(
        slug=f"proj-{uuid.uuid4()}", title="A Project", visibility=visibility
    )
    db_session.add(project)
    # commit (not flush): case_study.project_id is a real FK the DB checks
    # from the request's own separate session/connection, so this row must
    # be durably visible there, not just pending in this session's transaction.
    await db_session.commit()
    return project


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_list_case_studies_only_for_public_projects(
    db_session: AsyncSession,
) -> None:
    public_project = await _create_project(db_session, visibility="PUBLIC")
    private_project = await _create_project(db_session, visibility="PRIVATE")
    db_session.add_all(
        [
            CaseStudy(project_id=public_project.id, challenge="visible"),
            CaseStudy(project_id=private_project.id, challenge="hidden"),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/case-studies")

    assert response.status_code == 200
    challenges = {item["challenge"] for item in response.json()["data"]}
    assert challenges == {"visible"}


async def test_get_case_study_by_id(db_session: AsyncSession) -> None:
    project = await _create_project(db_session, visibility="PUBLIC")
    case_study = CaseStudy(
        project_id=project.id, challenge="c", solution="s", metrics={"uptime": "99.9%"}
    )
    db_session.add(case_study)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/case-studies/{case_study.id}")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["solution"] == "s"
    assert body["metrics"] == {"uptime": "99.9%"}


async def test_get_case_study_404_for_private_project(
    db_session: AsyncSession,
) -> None:
    project = await _create_project(db_session, visibility="PRIVATE")
    case_study = CaseStudy(project_id=project.id)
    db_session.add(case_study)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/case-studies/{case_study.id}")

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_get_case_study_404_for_unknown_id() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/case-studies/{uuid.uuid4()}")

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_admin_list_case_studies_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/case-studies")

    assert response.status_code == 401


async def test_admin_list_case_studies_includes_private_projects(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)
    public_project = await _create_project(db_session, visibility="PUBLIC")
    private_project = await _create_project(db_session, visibility="PRIVATE")
    db_session.add_all(
        [
            CaseStudy(project_id=public_project.id, challenge="visible"),
            CaseStudy(project_id=private_project.id, challenge="hidden"),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/case-studies", headers=_auth(token))

    assert response.status_code == 200
    challenges = {item["challenge"] for item in response.json()["data"]}
    assert challenges == {"visible", "hidden"}


@pytest.mark.usefixtures("db_session")
async def test_admin_get_case_study_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/admin/case-studies/{uuid.uuid4()}")

    assert response.status_code == 401


async def test_admin_get_case_study_returns_one_from_private_project(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)
    project = await _create_project(db_session, visibility="PRIVATE")
    case_study = CaseStudy(project_id=project.id, challenge="hidden")
    db_session.add(case_study)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/admin/case-studies/{case_study.id}", headers=_auth(token)
        )

    assert response.status_code == 200
    assert response.json()["data"]["challenge"] == "hidden"


async def test_admin_get_case_study_404_for_unknown_id(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/admin/case-studies/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_create_case_study_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/case-studies", json={"project_id": str(uuid.uuid4())}
        )

    assert response.status_code == 401


async def test_create_case_study_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    project = await _create_project(db_session, visibility="PUBLIC")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/case-studies",
            json={"project_id": str(project.id), "challenge": "scale"},
            headers=_auth(token),
        )

    assert response.status_code == 201
    assert response.json()["data"]["challenge"] == "scale"


async def test_create_case_study_404_for_unknown_project(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/case-studies",
            json={"project_id": str(uuid.uuid4())},
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_update_case_study_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    project = await _create_project(db_session, visibility="PUBLIC")
    case_study = CaseStudy(project_id=project.id, challenge="old")
    db_session.add(case_study)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/case-studies/{case_study.id}",
            json={"project_id": str(project.id), "challenge": "new"},
            headers=_auth(token),
        )

    assert response.status_code == 200
    assert response.json()["data"]["challenge"] == "new"


async def test_update_case_study_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    project = await _create_project(db_session, visibility="PUBLIC")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/case-studies/{uuid.uuid4()}",
            json={"project_id": str(project.id)},
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_delete_case_study_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    project = await _create_project(db_session, visibility="PUBLIC")
    case_study = CaseStudy(project_id=project.id)
    db_session.add(case_study)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/case-studies/{case_study.id}", headers=_auth(token)
        )

    assert response.status_code == 204


async def test_delete_case_study_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/case-studies/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404
