import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service


async def test_service_defaults(db_session: AsyncSession) -> None:
    service = Service(title="Automatización IA", slug="automatizacion-ia")
    db_session.add(service)
    await db_session.commit()

    assert service.featured is False
    assert service.active is True


async def test_service_slug_must_be_unique(db_session: AsyncSession) -> None:
    db_session.add(Service(title="A", slug="dup"))
    await db_session.commit()

    db_session.add(Service(title="B", slug="dup"))
    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_service_requires_a_title(db_session: AsyncSession) -> None:
    db_session.add(Service(title=None, slug="no-title"))
    with pytest.raises(IntegrityError):
        await db_session.commit()
