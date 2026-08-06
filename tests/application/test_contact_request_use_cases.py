from app.application.ports.contact_request_repository import ContactRequestInput
from app.application.use_cases.contact_requests import SubmitContactRequest
from app.domain.enums import ContactStatus
from tests.application.fakes import InMemoryContactRequestRepository


def _input(**overrides: object) -> ContactRequestInput:
    defaults: dict[str, object] = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "company": None,
        "subject": None,
        "message": "We'd like to talk about an automation project.",
    }
    defaults.update(overrides)
    return ContactRequestInput(**defaults)  # type: ignore[arg-type]


async def test_submit_contact_request_persists_it_through_the_repository() -> None:
    repo = InMemoryContactRequestRepository()
    use_case = SubmitContactRequest(repository=repo)

    result = await use_case.execute(_input(name="Grace Hopper"))

    assert result.name == "Grace Hopper"
    assert result.status is ContactStatus.NEW
    assert repo.created == [result]
