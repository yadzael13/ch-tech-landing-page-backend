from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db


async def test_get_db_yields_an_async_session() -> None:
    gen = get_db()

    session = await anext(gen)
    try:
        assert isinstance(session, AsyncSession)
    finally:
        await gen.aclose()
