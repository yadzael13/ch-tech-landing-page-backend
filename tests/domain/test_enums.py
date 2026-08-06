from app.domain.enums import (
    ContactStatus,
    ProductStatus,
    ProjectStatus,
    UserRole,
    Visibility,
)


def test_project_status_matches_data_model() -> None:
    assert {member.value for member in ProjectStatus} == {
        "PLANNING",
        "IN_PROGRESS",
        "COMPLETED",
        "ARCHIVED",
    }


def test_visibility_matches_data_model() -> None:
    assert {member.value for member in Visibility} == {"PUBLIC", "PRIVATE"}


def test_contact_status_matches_data_model() -> None:
    assert {member.value for member in ContactStatus} == {
        "NEW",
        "READ",
        "REPLIED",
        "ARCHIVED",
    }


def test_user_role_matches_data_model() -> None:
    assert {member.value for member in UserRole} == {"ADMIN"}


def test_product_status_matches_data_model() -> None:
    assert {member.value for member in ProductStatus} == {
        "WAITLIST",
        "BETA",
        "LIVE",
    }
