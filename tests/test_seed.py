import bcrypt
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.db.seed as seed_module
from app.core.config import get_settings
from app.db.seed import (
    TECHNOLOGY_CATALOG,
    main,
    seed_admin_user,
    seed_company,
    seed_team,
    seed_technologies,
)
from app.models import Company, TeamMember, Technology, User
from tests.conftest import async_session_factory as _test_session_factory


async def test_seed_admin_user_creates_a_working_login(
    db_session: AsyncSession,
) -> None:
    await seed_admin_user(db_session)
    await db_session.commit()

    settings = get_settings()
    result = await db_session.execute(
        select(User).where(User.email == settings.seed_admin_email)
    )
    admin = result.scalar_one()

    assert bcrypt.checkpw(
        settings.seed_admin_password.encode(), admin.password_hash.encode()
    )


async def test_seed_admin_user_is_idempotent(db_session: AsyncSession) -> None:
    await seed_admin_user(db_session)
    await seed_admin_user(db_session)
    await db_session.commit()

    count = await db_session.scalar(select(func.count()).select_from(User))

    assert count == 1


async def test_seed_technologies_is_idempotent(db_session: AsyncSession) -> None:
    await seed_technologies(db_session)
    await seed_technologies(db_session)
    await db_session.commit()

    count = await db_session.scalar(select(func.count()).select_from(Technology))
    result = await db_session.execute(select(Technology.name))
    names = {row[0] for row in result.all()}

    assert count == len(names)
    assert "Python" in names


async def test_seed_company_creates_the_singleton(db_session: AsyncSession) -> None:
    await seed_company(db_session)
    await db_session.commit()

    company = await db_session.scalar(select(Company))

    assert company is not None
    assert company.display_name == "CH-TECH"


async def test_seed_company_is_idempotent(db_session: AsyncSession) -> None:
    await seed_company(db_session)
    await seed_company(db_session)
    await db_session.commit()

    count = await db_session.scalar(select(func.count()).select_from(Company))

    assert count == 1


async def test_seed_team_creates_the_founder(db_session: AsyncSession) -> None:
    # seed_team links the founder to the seeded admin login (DATA_MODEL.md:
    # "Puede estar asociado a un User, si esa persona tiene acceso al panel
    # administrativo") — the admin user must exist first.
    await seed_admin_user(db_session)
    await db_session.flush()

    await seed_team(db_session)
    await db_session.commit()

    settings = get_settings()
    admin = await db_session.scalar(
        select(User).where(User.email == settings.seed_admin_email)
    )
    founder = await db_session.scalar(select(TeamMember))

    assert founder is not None
    assert founder.name == "Yadzael Chalico"
    assert founder.role == "Founder & Lead Software Engineer"
    assert founder.user_id == admin.id
    assert founder.display_order == 0
    assert founder.active is True


async def test_seed_team_is_idempotent(db_session: AsyncSession) -> None:
    await seed_admin_user(db_session)
    await db_session.flush()

    await seed_team(db_session)
    await seed_team(db_session)
    await db_session.commit()

    count = await db_session.scalar(select(func.count()).select_from(TeamMember))

    assert count == 1


async def test_main_seeds_admin_and_technologies(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    # main() otherwise opens its own session via app.db.session's factory,
    # which points at the real app database, not this test's — see
    # tests/conftest.py for why those must never be the same database.
    monkeypatch.setattr(seed_module, "async_session_factory", _test_session_factory)

    await main()

    settings = get_settings()
    user_count = await db_session.scalar(select(func.count()).select_from(User))
    tech_count = await db_session.scalar(select(func.count()).select_from(Technology))
    company_count = await db_session.scalar(select(func.count()).select_from(Company))
    team_count = await db_session.scalar(select(func.count()).select_from(TeamMember))

    assert user_count == 1
    assert tech_count == len(TECHNOLOGY_CATALOG)
    assert company_count == 1
    assert team_count == 1
    admin = await db_session.scalar(
        select(User).where(User.email == settings.seed_admin_email)
    )
    assert admin is not None
    founder = await db_session.scalar(select(TeamMember))
    assert founder is not None
    assert founder.user_id == admin.id
