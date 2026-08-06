import uuid
from datetime import UTC, datetime

from app.domain.case_study import CaseStudy


def _case_study(**overrides: object) -> CaseStudy:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "project_id": uuid.uuid4(),
        "challenge": "Scale the platform",
        "solution": "Clean Architecture",
        "architecture": None,
        "lessons_learned": None,
        "metrics": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return CaseStudy(**defaults)  # type: ignore[arg-type]


def test_case_study_belongs_to_a_project() -> None:
    project_id = uuid.uuid4()
    assert _case_study(project_id=project_id).project_id == project_id


def test_case_study_metrics_is_an_optional_mapping() -> None:
    case_study = _case_study(metrics={"loc": 1200, "coverage": 0.93})
    assert case_study.metrics == {"loc": 1200, "coverage": 0.93}
