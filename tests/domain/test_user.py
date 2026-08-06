import uuid
from datetime import UTC, datetime

from app.domain.enums import UserRole
from app.domain.user import User
from app.domain.value_objects import Email


def _user(**overrides: object) -> User:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "name": "Yadzael Chalico",
        "email": Email("yadzael@ch-tech.dev"),
        "password_hash": "bcrypt-hash",
        "role": UserRole.ADMIN,
        "is_active": True,
        "last_login": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return User(**defaults)  # type: ignore[arg-type]


def test_user_holds_an_email_value_object() -> None:
    user = _user()
    assert isinstance(user.email, Email)
    assert str(user.email) == "yadzael@ch-tech.dev"


def test_user_role_is_admin_only() -> None:
    assert _user().role is UserRole.ADMIN
