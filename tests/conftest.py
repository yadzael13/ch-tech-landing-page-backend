from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app


def _resolve_test_database_url() -> str:
    """Tests must never run against the same database the running app
    uses — db_session below creates/drops every table on every test, and
    doing that against the app's real database is what previously wiped
    the dev DB out from under the running backend. Always <db>_test,
    derived from MIGRATION_DATABASE_URL (not DATABASE_URL): every fixture
    below performs DDL (CREATE DATABASE, create_all/drop_all), which the
    app's own chtech_app credential deliberately cannot do (see
    docs/adr/0001-mysql-database-privilege-separation.md) — this is an
    intentional, test-scoped exception to that boundary, not a loosening
    of it. So no extra config is needed in dev or CI."""
    url = make_url(get_settings().migration_database_url)
    if not url.database:
        raise RuntimeError("MIGRATION_DATABASE_URL must include a database name")
    test_name = (
        url.database if url.database.endswith("_test") else f"{url.database}_test"
    )
    return url.set(database=test_name).render_as_string(hide_password=False)


_TEST_DATABASE_URL = _resolve_test_database_url()
_TEST_DATABASE_NAME = make_url(_TEST_DATABASE_URL).database

# Guard rail: everything below operates by dropping and recreating every
# table. Refuse to even start if that database doesn't unambiguously look
# disposable, so a future change to the derivation above fails loudly
# instead of quietly pointing tests at a real database again.
if not _TEST_DATABASE_NAME or not _TEST_DATABASE_NAME.endswith("_test"):
    raise RuntimeError(
        f"Refusing to run tests against database {_TEST_DATABASE_NAME!r} — "
        "it doesn't look like a disposable test database (expected a name "
        "ending in '_test')."
    )

# Module-level singleton, same reasoning as app.db.session.engine: every
# async test must share the event loop it was created on.
engine = create_async_engine(_TEST_DATABASE_URL)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _ensure_test_database_exists() -> AsyncGenerator[None]:
    admin_engine = create_async_engine(
        get_settings().migration_database_url, isolation_level="AUTOCOMMIT"
    )
    async with admin_engine.connect() as conn:
        exists = await conn.scalar(
            text(
                "SELECT SCHEMA_NAME FROM information_schema.schemata "
                "WHERE SCHEMA_NAME = :name"
            ),
            {"name": _TEST_DATABASE_NAME},
        )
        if not exists:
            # Identifier can't be parameterized — _TEST_DATABASE_NAME is
            # derived from our own config above, never from user input.
            # Backtick-quoted (MySQL identifier quoting), not double-quoted
            # (Postgres-style — only valid under MySQL's non-default
            # ANSI_QUOTES sql_mode).
            await conn.execute(text(f"CREATE DATABASE `{_TEST_DATABASE_NAME}`"))
    await admin_engine.dispose()
    yield


async def _get_test_db() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _use_test_database_for_the_app(
    _ensure_test_database_exists: None,
) -> AsyncGenerator[None]:
    # Every test hits the app over ASGITransport, which resolves
    # Depends(get_db) through app.db.session's own factory unless
    # overridden — without this, HTTP requests in tests would read/write
    # the real app database while db_session-based setup/assertions in the
    # same test operate on the separate test one.
    fastapi_app.dependency_overrides[get_db] = _get_test_db
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    # Model/constraint tests get a real, throwaway schema: created fresh from
    # Base.metadata before the test and dropped after, so they never depend on
    # (or pollute) whatever migration state the dev database happens to be in.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
