import uuid
from datetime import UTC, datetime

from app.domain.company import Company
from app.domain.value_objects import Email


def _company(**overrides: object) -> Company:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "legal_name": "CH-TECH S.A. de C.V.",
        "display_name": "CH-TECH",
        "tagline": None,
        "mission": None,
        "vision": None,
        "email": None,
        "phone": None,
        "address": None,
        "social_links": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Company(**defaults)  # type: ignore[arg-type]


def test_company_holds_an_email_value_object_when_present() -> None:
    company = _company(email=Email("hello@ch-tech.dev"))
    assert isinstance(company.email, Email)


def test_company_social_links_is_an_optional_mapping() -> None:
    company = _company(social_links={"github": "https://github.com/ch-tech"})
    assert company.social_links == {"github": "https://github.com/ch-tech"}
