from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

engine = create_async_engine(
    get_settings().database_url,
    # Explicit rather than SQLAlchemy's defaults (pool_size=5,
    # max_overflow=10, no pre-ping): several Uvicorn workers each get their
    # own engine, so the implicit default undercounts real concurrent
    # capacity in production.
    pool_size=10,
    max_overflow=20,
    # Without this, a connection silently closed by an intermediary
    # (RDS/Aurora MySQL, a cloud LB idle timeout) surfaces as a confusing
    # error on whatever request next tries to use it — pre-ping validates
    # with a cheap round trip before handing the connection out.
    pool_pre_ping=True,
    # Recycle before RDS/Aurora MySQL's own wait_timeout cutoff, so
    # connections are refreshed proactively rather than found dead.
    pool_recycle=1800,
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
