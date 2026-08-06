import uuid
from datetime import UTC, datetime

from app.domain.team_member import TeamMember
from app.domain.value_objects import Image, Url


def _team_member(**overrides: object) -> TeamMember:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "user_id": None,
        "name": "Yadzael Chalico",
        "role": "Founder & Lead Software Engineer",
        "bio": None,
        "photo": None,
        "linkedin_url": None,
        "github_url": None,
        "display_order": 0,
        "active": True,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return TeamMember(**defaults)  # type: ignore[arg-type]


def test_team_member_can_exist_without_a_user_account() -> None:
    assert _team_member(user_id=None).user_id is None


def test_team_member_can_be_linked_to_a_user_account() -> None:
    user_id = uuid.uuid4()
    assert _team_member(user_id=user_id).user_id == user_id


def test_team_member_urls_are_value_objects_when_present() -> None:
    member = _team_member(
        photo=Image("https://ch-tech.dev/team/yadzael.jpg"),
        linkedin_url=Url("https://linkedin.com/in/yadzael"),
        github_url=Url("https://github.com/yadzael13"),
    )
    assert isinstance(member.photo, Image)
    assert isinstance(member.linkedin_url, Url)
    assert isinstance(member.github_url, Url)
