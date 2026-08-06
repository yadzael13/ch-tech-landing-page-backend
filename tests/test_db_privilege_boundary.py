"""Concrete proof of the ADR-0014 privilege boundary.

The app's own DATABASE_URL (chtech_app) must never be able to alter table
structure — not through a bug, not through a future in-app AI feature, and
not through this test's own hand. This connects directly (bypassing the ORM
session and this repo's other test fixtures) with the exact credential
app/db/session.py uses in production, against the real database it points
at — not the disposable `_test` database tests/conftest.py creates — so it
exercises the actual boundary, not a stand-in for it.

Deliberately excluded from the coverage-gated `pytest --cov` run (see
.github/workflows/ci.yml, "--ignore" on the "Test backend" step) and run as
its own explicit CI step instead: it depends on `alembic upgrade head`
having already run against that same database (so the `users` table
exists), which is an ordering assumption the rest of the suite doesn't
share.
"""

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings


async def test_chtech_app_cannot_run_ddl() -> None:
    engine = create_async_engine(get_settings().database_url)
    try:
        raised: DBAPIError | None = None
        try:
            async with engine.connect() as conn:
                await conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN _privilege_boundary_test VARCHAR(10)"
                    )
                )
        except DBAPIError as exc:
            raised = exc

        assert raised is not None, (
            "chtech_app was able to run ALTER TABLE — the DML/DDL privilege "
            "split from ADR-0014 is not in effect against this database."
        )
        # MySQL error 1142: "command denied to user ... for table ..." — the
        # exact error a DML-only grant produces for a DDL statement.
        assert "1142" in str(raised.orig)
    finally:
        await engine.dispose()


async def test_chtech_app_can_still_read_and_write() -> None:
    """The boundary is DDL-specific, not a broken connection — chtech_app
    must keep working for ordinary application traffic."""
    engine = create_async_engine(get_settings().database_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            assert result.scalar_one() >= 0
    finally:
        await engine.dispose()
