from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.company_repository import CompanyInput
from app.infrastructure.repositories.company_repository import (
    SQLAlchemyCompanyRepository,
)


def _input(**overrides: object) -> CompanyInput:
    defaults: dict[str, object] = {
        "legal_name": "CH-TECH",
        "display_name": "CH-TECH",
        "tagline": None,
        "mission": None,
        "vision": None,
    }
    defaults.update(overrides)
    return CompanyInput(**defaults)  # type: ignore[arg-type]


async def test_get_returns_none_when_no_row_exists(db_session: AsyncSession) -> None:
    repo = SQLAlchemyCompanyRepository(db_session)
    assert await repo.get() is None


async def test_update_creates_the_row_when_missing(db_session: AsyncSession) -> None:
    repo = SQLAlchemyCompanyRepository(db_session)

    result = await repo.update(_input(tagline="Building software."))

    assert result.tagline == "Building software."
    found = await repo.get()
    assert found is not None
    assert found.id == result.id


async def test_update_replaces_the_existing_row_in_place(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyCompanyRepository(db_session)
    first = await repo.update(_input(tagline="Old tagline"))

    second = await repo.update(_input(tagline="New tagline"))

    assert second.id == first.id
    assert second.tagline == "New tagline"


async def test_round_trip_preserves_email_and_social_links(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyCompanyRepository(db_session)

    await repo.update(
        _input(
            email="hello@ch-tech.dev",
            social_links={"github": "https://github.com/ch-tech"},
        )
    )

    found = await repo.get()

    assert found is not None
    assert str(found.email) == "hello@ch-tech.dev"
    assert found.social_links == {"github": "https://github.com/ch-tech"}
