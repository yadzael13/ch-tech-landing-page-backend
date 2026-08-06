import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.application.ports.case_study_repository import CaseStudyInput
from app.application.use_cases.case_studies import (
    CreateCaseStudy,
    DeleteCaseStudy,
    GetCaseStudyById,
    ListCaseStudies,
    UpdateCaseStudy,
)
from app.core.rate_limit import ip_rate_limiter
from app.db.session import get_db
from app.domain.case_study import CaseStudy
from app.infrastructure.repositories.case_study_repository import (
    SQLAlchemyCaseStudyRepository,
)
from app.infrastructure.repositories.project_repository import (
    SQLAlchemyProjectRepository,
)
from app.schemas.case_study import CaseStudyItem, CaseStudyWrite
from app.schemas.response import SuccessResponse

public_router = APIRouter(prefix="/case-studies", tags=["case-studies"])
admin_router = APIRouter(prefix="/admin/case-studies", tags=["admin:case-studies"])

# API.md "Rate Limiting" -> "API Pública": 100 requests/minute/IP.
_public_api_limit = Depends(
    ip_rate_limiter(limit=100, window_seconds=60, scope="public-api")
)

# Admin writes are auth-gated but otherwise had no throttle — a leaked
# access token could hammer these without limit (OWASP API4:2023).
_admin_write_limit = Depends(
    ip_rate_limiter(limit=60, window_seconds=60, scope="admin-write")
)


def _list_use_case(session: AsyncSession = Depends(get_db)) -> ListCaseStudies:
    return ListCaseStudies(repository=SQLAlchemyCaseStudyRepository(session))


def _get_by_id_use_case(session: AsyncSession = Depends(get_db)) -> GetCaseStudyById:
    return GetCaseStudyById(repository=SQLAlchemyCaseStudyRepository(session))


def _create_use_case(session: AsyncSession = Depends(get_db)) -> CreateCaseStudy:
    return CreateCaseStudy(
        repository=SQLAlchemyCaseStudyRepository(session),
        project_repository=SQLAlchemyProjectRepository(session),
    )


def _update_use_case(session: AsyncSession = Depends(get_db)) -> UpdateCaseStudy:
    return UpdateCaseStudy(
        repository=SQLAlchemyCaseStudyRepository(session),
        project_repository=SQLAlchemyProjectRepository(session),
    )


def _delete_use_case(session: AsyncSession = Depends(get_db)) -> DeleteCaseStudy:
    return DeleteCaseStudy(repository=SQLAlchemyCaseStudyRepository(session))


def _to_item(case_study: CaseStudy) -> CaseStudyItem:
    return CaseStudyItem(
        id=case_study.id,
        project_id=case_study.project_id,
        challenge=case_study.challenge,
        solution=case_study.solution,
        architecture=case_study.architecture,
        lessons_learned=case_study.lessons_learned,
        metrics=case_study.metrics,
        created_at=case_study.created_at,
        updated_at=case_study.updated_at,
    )


def _to_input(payload: CaseStudyWrite) -> CaseStudyInput:
    return CaseStudyInput(
        project_id=payload.project_id,
        challenge=payload.challenge,
        solution=payload.solution,
        architecture=payload.architecture,
        lessons_learned=payload.lessons_learned,
        metrics=payload.metrics,
    )


@public_router.get("", dependencies=[_public_api_limit])
async def list_case_studies(
    use_case: ListCaseStudies = Depends(_list_use_case),
) -> SuccessResponse[list[CaseStudyItem]]:
    case_studies = await use_case.execute(public_only=True)
    return SuccessResponse(data=[_to_item(c) for c in case_studies])


@public_router.get("/{case_study_id}", dependencies=[_public_api_limit])
async def get_case_study(
    case_study_id: uuid.UUID,
    use_case: GetCaseStudyById = Depends(_get_by_id_use_case),
) -> SuccessResponse[CaseStudyItem]:
    case_study = await use_case.execute(case_study_id, public_only=True)
    return SuccessResponse(data=_to_item(case_study))


@admin_router.get("")
async def list_admin_case_studies(
    _current_user_id: str = Depends(get_current_user_id),
    use_case: ListCaseStudies = Depends(_list_use_case),
) -> SuccessResponse[list[CaseStudyItem]]:
    """Same shape as GET /case-studies, minus the join filter on
    Project.visibility == "PUBLIC" — the admin management table needs case
    studies attached to private/draft projects too."""
    case_studies = await use_case.execute(public_only=False)
    return SuccessResponse(data=[_to_item(c) for c in case_studies])


@admin_router.get("/{case_study_id}")
async def get_admin_case_study(
    case_study_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: GetCaseStudyById = Depends(_get_by_id_use_case),
) -> SuccessResponse[CaseStudyItem]:
    """Same shape as GET /case-studies/{id}, but without the join filter on
    the linked project's visibility."""
    case_study = await use_case.execute(case_study_id, public_only=False)
    return SuccessResponse(data=_to_item(case_study))


@admin_router.post("", status_code=201, dependencies=[_admin_write_limit])
async def create_case_study(
    payload: CaseStudyWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: CreateCaseStudy = Depends(_create_use_case),
) -> SuccessResponse[CaseStudyItem]:
    case_study = await use_case.execute(_to_input(payload))
    return SuccessResponse(data=_to_item(case_study))


@admin_router.put("/{case_study_id}", dependencies=[_admin_write_limit])
async def update_case_study(
    case_study_id: uuid.UUID,
    payload: CaseStudyWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: UpdateCaseStudy = Depends(_update_use_case),
) -> SuccessResponse[CaseStudyItem]:
    case_study = await use_case.execute(case_study_id, _to_input(payload))
    return SuccessResponse(data=_to_item(case_study))


@admin_router.delete(
    "/{case_study_id}", status_code=204, dependencies=[_admin_write_limit]
)
async def delete_case_study(
    case_study_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: DeleteCaseStudy = Depends(_delete_use_case),
) -> None:
    await use_case.execute(case_study_id)
