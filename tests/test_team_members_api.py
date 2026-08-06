import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import get_redis
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import TeamMember, User


async def _create_admin(db_session: AsyncSession) -> str:
    user = User(
        name="Admin",
        email=f"{uuid.uuid4()}@ch-tech.dev",
        password_hash=hash_password("s3cret-pass"),
    )
    db_session.add(user)
    await db_session.flush()
    return create_access_token(subject=str(user.id), role=user.role)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_list_team_members_only_returns_active(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            TeamMember(name="Active One", role="Engineer", active=True),
            TeamMember(name="Inactive One", role="Engineer", active=False),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/team")

    assert response.status_code == 200
    names = {item["name"] for item in response.json()["data"]}
    assert names == {"Active One"}


async def test_get_team_member_by_id_returns_full_detail(
    db_session: AsyncSession,
) -> None:
    member = TeamMember(name="Yadzael Chalico", role="Founder & Lead Software Engineer")
    db_session.add(member)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/team/{member.id}")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Yadzael Chalico"


async def test_get_team_member_404_for_inactive(db_session: AsyncSession) -> None:
    member = TeamMember(name="Hidden", role="Engineer", active=False)
    db_session.add(member)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/team/{member.id}")

    assert response.status_code == 404


@pytest.mark.usefixtures("db_session")
async def test_admin_list_team_members_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/team")

    assert response.status_code == 401


async def test_admin_list_team_members_includes_inactive(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)
    db_session.add_all(
        [
            TeamMember(name="Active One", role="Engineer", active=True),
            TeamMember(name="Inactive One", role="Engineer", active=False),
        ]
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/team", headers=_auth(token))

    assert response.status_code == 200
    names = {item["name"] for item in response.json()["data"]}
    assert names == {"Active One", "Inactive One"}


async def test_admin_get_team_member_returns_inactive_by_id(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)
    member = TeamMember(name="Hidden", role="Engineer", active=False)
    db_session.add(member)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/admin/team/{member.id}", headers=_auth(token)
        )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Hidden"


@pytest.mark.usefixtures("db_session")
async def test_create_team_member_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/team", json={"name": "New Member", "role": "Engineer"}
        )

    assert response.status_code == 401


async def test_create_team_member_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/team",
            json={"name": "Brand New", "role": "Engineer"},
            headers=_auth(token),
        )

    assert response.status_code == 201
    assert response.json()["data"]["name"] == "Brand New"


async def test_create_team_member_rejects_an_unknown_user(
    db_session: AsyncSession,
) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/team",
            json={
                "name": "New Member",
                "role": "Engineer",
                "user_id": str(uuid.uuid4()),
            },
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_update_team_member_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    entity = TeamMember(name="Old Name", role="Engineer")
    db_session.add(entity)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/team/{entity.id}",
            json={"name": "New Name", "role": "Engineer"},
            headers=_auth(token),
        )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "New Name"


async def test_update_team_member_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/admin/team/{uuid.uuid4()}",
            json={"name": "Whatever", "role": "Whatever"},
            headers=_auth(token),
        )

    assert response.status_code == 404


async def test_delete_team_member_succeeds_as_admin(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    entity = TeamMember(name="To Delete", role="Engineer")
    db_session.add(entity)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/team/{entity.id}", headers=_auth(token)
        )

    assert response.status_code == 204


async def test_delete_team_member_404_for_unknown_id(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/admin/team/{uuid.uuid4()}", headers=_auth(token)
        )

    assert response.status_code == 404


async def test_admin_writes_are_rate_limited(db_session: AsyncSession) -> None:
    token = await _create_admin(db_session)
    # "admin-write" is one shared counter per IP across every admin router
    # (by design — it's a blanket abuse guard, not per-resource). Other
    # tests in the suite hit admin write endpoints from the same test-client
    # IP, so reset the window right before the burst instead of assuming it
    # starts at zero.
    await get_redis().delete("ratelimit:admin-write:127.0.0.1")

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(60):
                response = await client.post(
                    "/api/v1/admin/team",
                    json={"name": "Member", "role": "Engineer"},
                    headers=_auth(token),
                )
                assert response.status_code == 201

            over_limit = await client.post(
                "/api/v1/admin/team",
                json={"name": "Member", "role": "Engineer"},
                headers=_auth(token),
            )

        assert over_limit.status_code == 429
        assert over_limit.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    finally:
        await get_redis().delete("ratelimit:admin-write:127.0.0.1")
