import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.application.ports.project_repository import (
    ProjectFilters,
    ProjectInput,
    ProjectWithTechnologies,
)
from app.application.use_cases.projects import (
    CreateProject,
    DeleteProject,
    GetProjectById,
    GetProjectBySlug,
    ListProjects,
    UpdateProject,
)
from app.core.rate_limit import ip_rate_limiter
from app.db.session import get_db
from app.domain.enums import ProjectStatus, Visibility
from app.domain.technology import Technology
from app.infrastructure.repositories.project_repository import (
    SQLAlchemyProjectRepository,
)
from app.schemas.project import (
    ProjectDetail,
    ProjectListItem,
    ProjectWrite,
    TechnologySummary,
)
from app.schemas.response import SuccessResponse

public_router = APIRouter(prefix="/projects", tags=["projects"])
admin_router = APIRouter(prefix="/admin/projects", tags=["admin:projects"])

# API.md "Rate Limiting" -> "API Pública": 100 requests/minute/IP.
_public_api_limit = Depends(
    ip_rate_limiter(limit=100, window_seconds=60, scope="public-api")
)

# Admin writes are auth-gated but otherwise had no throttle — a leaked
# access token could hammer these without limit (OWASP API4:2023).
_admin_write_limit = Depends(
    ip_rate_limiter(limit=60, window_seconds=60, scope="admin-write")
)


def _list_projects_use_case(session: AsyncSession = Depends(get_db)) -> ListProjects:
    return ListProjects(repository=SQLAlchemyProjectRepository(session))


def _get_project_by_slug_use_case(
    session: AsyncSession = Depends(get_db),
) -> GetProjectBySlug:
    return GetProjectBySlug(repository=SQLAlchemyProjectRepository(session))


def _get_project_by_id_use_case(
    session: AsyncSession = Depends(get_db),
) -> GetProjectById:
    return GetProjectById(repository=SQLAlchemyProjectRepository(session))


def _create_project_use_case(
    session: AsyncSession = Depends(get_db),
) -> CreateProject:
    return CreateProject(repository=SQLAlchemyProjectRepository(session))


def _update_project_use_case(
    session: AsyncSession = Depends(get_db),
) -> UpdateProject:
    return UpdateProject(repository=SQLAlchemyProjectRepository(session))


def _delete_project_use_case(
    session: AsyncSession = Depends(get_db),
) -> DeleteProject:
    return DeleteProject(repository=SQLAlchemyProjectRepository(session))


def _to_technology_summary(technology: Technology) -> TechnologySummary:
    return TechnologySummary(
        id=technology.id, name=technology.name, category=technology.category
    )


def _to_list_item(row: ProjectWithTechnologies) -> ProjectListItem:
    return ProjectListItem(
        id=row.project.id,
        slug=str(row.project.slug),
        title=row.project.title,
        featured=row.project.featured,
    )


def _to_detail(row: ProjectWithTechnologies) -> ProjectDetail:
    project = row.project
    return ProjectDetail(
        id=project.id,
        slug=str(project.slug),
        title=project.title,
        short_description=project.short_description,
        full_description=project.full_description,
        repository_url=str(project.repository_url) if project.repository_url else None,
        live_demo_url=str(project.live_demo_url) if project.live_demo_url else None,
        cover_image=str(project.cover_image) if project.cover_image else None,
        status=project.status.value,
        visibility=project.visibility.value,
        featured=project.featured,
        started_at=project.started_at,
        finished_at=project.finished_at,
        technologies=[_to_technology_summary(t) for t in row.technologies],
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _to_project_input(payload: ProjectWrite) -> ProjectInput:
    return ProjectInput(
        slug=payload.slug,
        title=payload.title,
        short_description=payload.short_description,
        full_description=payload.full_description,
        repository_url=payload.repository_url,
        live_demo_url=payload.live_demo_url,
        cover_image=payload.cover_image,
        status=ProjectStatus(payload.status.value),
        visibility=Visibility(payload.visibility.value),
        featured=payload.featured,
        started_at=payload.started_at,
        finished_at=payload.finished_at,
        technology_ids=payload.technology_ids,
    )


def _to_filters(
    *,
    page: int,
    limit: int,
    technology: str | None,
    featured: bool | None,
    status: str | None,
    search: str | None,
    sort: str,
) -> ProjectFilters:
    return ProjectFilters(
        technology=technology,
        featured=featured,
        status=status,
        search=search,
        sort=sort,
        page=page,
        limit=limit,
    )


@public_router.get("", dependencies=[_public_api_limit])
async def list_projects(
    use_case: ListProjects = Depends(_list_projects_use_case),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    technology: str | None = None,
    featured: bool | None = None,
    status: str | None = None,
    search: str | None = None,
    sort: str = Query(default="created_at", pattern="^(created_at|title)$"),
) -> SuccessResponse[list[ProjectListItem]]:
    filters = _to_filters(
        page=page,
        limit=limit,
        technology=technology,
        featured=featured,
        status=status,
        search=search,
        sort=sort,
    )
    rows = await use_case.execute(filters, public_only=True)
    return SuccessResponse(data=[_to_list_item(row) for row in rows])


@public_router.get("/{slug}", dependencies=[_public_api_limit])
async def get_project(
    slug: str, use_case: GetProjectBySlug = Depends(_get_project_by_slug_use_case)
) -> SuccessResponse[ProjectDetail]:
    row = await use_case.execute(slug, public_only=True)
    return SuccessResponse(data=_to_detail(row))


@admin_router.get("")
async def list_admin_projects(
    _current_user_id: str = Depends(get_current_user_id),
    use_case: ListProjects = Depends(_list_projects_use_case),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    technology: str | None = None,
    featured: bool | None = None,
    status: str | None = None,
    search: str | None = None,
    sort: str = Query(default="created_at", pattern="^(created_at|title)$"),
) -> SuccessResponse[list[ProjectDetail]]:
    """Same shape/filters as GET /projects, minus the visibility=PUBLIC
    filter — the admin management table needs to see drafts/private
    projects too, which the public endpoint deliberately hides. Returns the
    full ProjectDetail shape (not the public ProjectListItem) since the
    management table also needs status/visibility, which the public list
    intentionally omits."""
    filters = _to_filters(
        page=page,
        limit=limit,
        technology=technology,
        featured=featured,
        status=status,
        search=search,
        sort=sort,
    )
    rows = await use_case.execute(filters, public_only=False)
    return SuccessResponse(data=[_to_detail(row) for row in rows])


@admin_router.get("/{project_id}")
async def get_admin_project(
    project_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: GetProjectById = Depends(_get_project_by_id_use_case),
) -> SuccessResponse[ProjectDetail]:
    """Same shape as GET /projects/{slug}, but by id and without the
    visibility filter — lets the edit form load a private/draft project
    the public detail endpoint would 404 on."""
    row = await use_case.execute(project_id)
    return SuccessResponse(data=_to_detail(row))


@admin_router.post("", status_code=201, dependencies=[_admin_write_limit])
async def create_project(
    payload: ProjectWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: CreateProject = Depends(_create_project_use_case),
) -> SuccessResponse[ProjectDetail]:
    row = await use_case.execute(_to_project_input(payload))
    return SuccessResponse(data=_to_detail(row))


@admin_router.put("/{project_id}", dependencies=[_admin_write_limit])
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: UpdateProject = Depends(_update_project_use_case),
) -> SuccessResponse[ProjectDetail]:
    row = await use_case.execute(project_id, _to_project_input(payload))
    return SuccessResponse(data=_to_detail(row))


@admin_router.delete(
    "/{project_id}", status_code=204, dependencies=[_admin_write_limit]
)
async def delete_project(
    project_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: DeleteProject = Depends(_delete_project_use_case),
) -> None:
    await use_case.execute(project_id)
