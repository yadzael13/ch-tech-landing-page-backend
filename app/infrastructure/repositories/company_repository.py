"""SQLAlchemy adapter for the CompanyRepository port (ADR-0012, Fase 6).

Company is a singleton — update() upserts: the first call creates the
row (normally already done by app.db.seed on startup), later calls
update the same row in place.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.company_repository import CompanyInput
from app.domain.company import Company as CompanyEntity
from app.domain.value_objects import Email
from app.models import Company as CompanyModel


def _to_entity(model: CompanyModel) -> CompanyEntity:
    return CompanyEntity(
        id=model.id,
        legal_name=model.legal_name,
        display_name=model.display_name,
        tagline=model.tagline,
        mission=model.mission,
        vision=model.vision,
        email=Email(model.email) if model.email else None,
        phone=model.phone,
        address=model.address,
        social_links=model.social_links,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyCompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> CompanyEntity | None:
        result = await self._session.execute(select(CompanyModel).limit(1))
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def update(self, data: CompanyInput) -> CompanyEntity:
        result = await self._session.execute(select(CompanyModel).limit(1))
        model = result.scalar_one_or_none()
        if model is None:
            model = CompanyModel()
            self._session.add(model)

        model.legal_name = data.legal_name
        model.display_name = data.display_name
        model.tagline = data.tagline
        model.mission = data.mission
        model.vision = data.vision
        model.email = data.email
        model.phone = data.phone
        model.address = data.address
        model.social_links = data.social_links

        await self._session.commit()
        await self._session.refresh(model)
        return _to_entity(model)
