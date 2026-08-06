import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.application.ports.article_repository import (
    ArticleInput,
    ArticleWithTechnologies,
)
from app.application.use_cases.articles import (
    CreateArticle,
    DeleteArticle,
    GetArticleById,
    GetArticleBySlug,
    ListArticles,
    UpdateArticle,
)
from app.core.rate_limit import ip_rate_limiter
from app.db.session import get_db
from app.domain.technology import Technology
from app.infrastructure.repositories.article_repository import (
    SQLAlchemyArticleRepository,
)
from app.schemas.article import ArticleDetail, ArticleListItem, ArticleWrite
from app.schemas.project import TechnologySummary
from app.schemas.response import SuccessResponse

public_router = APIRouter(prefix="/articles", tags=["articles"])
admin_router = APIRouter(prefix="/admin/articles", tags=["admin:articles"])

# API.md "Rate Limiting" -> "API Pública": 100 requests/minute/IP.
_public_api_limit = Depends(
    ip_rate_limiter(limit=100, window_seconds=60, scope="public-api")
)

# Admin writes are auth-gated but otherwise had no throttle — a leaked
# access token could hammer these without limit (OWASP API4:2023).
_admin_write_limit = Depends(
    ip_rate_limiter(limit=60, window_seconds=60, scope="admin-write")
)


def _list_use_case(session: AsyncSession = Depends(get_db)) -> ListArticles:
    return ListArticles(repository=SQLAlchemyArticleRepository(session))


def _get_by_slug_use_case(session: AsyncSession = Depends(get_db)) -> GetArticleBySlug:
    return GetArticleBySlug(repository=SQLAlchemyArticleRepository(session))


def _get_by_id_use_case(session: AsyncSession = Depends(get_db)) -> GetArticleById:
    return GetArticleById(repository=SQLAlchemyArticleRepository(session))


def _create_use_case(session: AsyncSession = Depends(get_db)) -> CreateArticle:
    return CreateArticle(repository=SQLAlchemyArticleRepository(session))


def _update_use_case(session: AsyncSession = Depends(get_db)) -> UpdateArticle:
    return UpdateArticle(repository=SQLAlchemyArticleRepository(session))


def _delete_use_case(session: AsyncSession = Depends(get_db)) -> DeleteArticle:
    return DeleteArticle(repository=SQLAlchemyArticleRepository(session))


def _to_technology_summary(technology: Technology) -> TechnologySummary:
    return TechnologySummary(
        id=technology.id, name=technology.name, category=technology.category
    )


def _to_list_item(row: ArticleWithTechnologies) -> ArticleListItem:
    article = row.article
    return ArticleListItem(
        id=article.id,
        slug=str(article.slug),
        title=article.title,
        summary=article.summary,
        cover_image=str(article.cover_image) if article.cover_image else None,
        reading_time=article.reading_time,
        published_at=article.published_at,
    )


def _to_detail(row: ArticleWithTechnologies) -> ArticleDetail:
    article = row.article
    return ArticleDetail(
        id=article.id,
        slug=str(article.slug),
        title=article.title,
        summary=article.summary,
        content=str(article.content),
        cover_image=str(article.cover_image) if article.cover_image else None,
        reading_time=article.reading_time,
        published=article.published,
        published_at=article.published_at,
        author_id=article.author_id,
        technologies=[_to_technology_summary(t) for t in row.technologies],
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


def _to_input(payload: ArticleWrite) -> ArticleInput:
    return ArticleInput(
        slug=payload.slug,
        title=payload.title,
        summary=payload.summary,
        content=payload.content,
        cover_image=payload.cover_image,
        reading_time=payload.reading_time,
        published=payload.published,
        published_at=payload.published_at,
        technology_ids=payload.technology_ids,
    )


@public_router.get("", dependencies=[_public_api_limit])
async def list_articles(
    use_case: ListArticles = Depends(_list_use_case),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> SuccessResponse[list[ArticleListItem]]:
    rows = await use_case.execute(published_only=True, page=page, limit=limit)
    return SuccessResponse(data=[_to_list_item(row) for row in rows])


@public_router.get("/{slug}", dependencies=[_public_api_limit])
async def get_article(
    slug: str, use_case: GetArticleBySlug = Depends(_get_by_slug_use_case)
) -> SuccessResponse[ArticleDetail]:
    row = await use_case.execute(slug, published_only=True)
    return SuccessResponse(data=_to_detail(row))


@admin_router.get("")
async def list_admin_articles(
    _current_user_id: str = Depends(get_current_user_id),
    use_case: ListArticles = Depends(_list_use_case),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> SuccessResponse[list[ArticleDetail]]:
    """Same filters as GET /articles, minus the published=True filter — the
    admin management table needs to see drafts too. Returns the full
    ArticleDetail shape (not the public ArticleListItem) since the table
    needs the explicit `published` flag, which the public list omits."""
    rows = await use_case.execute(published_only=False, page=page, limit=limit)
    return SuccessResponse(data=[_to_detail(row) for row in rows])


@admin_router.get("/{article_id}")
async def get_admin_article(
    article_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: GetArticleById = Depends(_get_by_id_use_case),
) -> SuccessResponse[ArticleDetail]:
    """Same shape as GET /articles/{slug}, but by id and without the
    published filter — lets the edit form load a draft the public detail
    endpoint would 404 on."""
    row = await use_case.execute(article_id)
    return SuccessResponse(data=_to_detail(row))


@admin_router.post("", status_code=201, dependencies=[_admin_write_limit])
async def create_article(
    payload: ArticleWrite,
    current_user_id: str = Depends(get_current_user_id),
    use_case: CreateArticle = Depends(_create_use_case),
) -> SuccessResponse[ArticleDetail]:
    row = await use_case.execute(
        _to_input(payload), author_id=uuid.UUID(current_user_id)
    )
    return SuccessResponse(data=_to_detail(row))


@admin_router.put("/{article_id}", dependencies=[_admin_write_limit])
async def update_article(
    article_id: uuid.UUID,
    payload: ArticleWrite,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: UpdateArticle = Depends(_update_use_case),
) -> SuccessResponse[ArticleDetail]:
    row = await use_case.execute(article_id, _to_input(payload))
    return SuccessResponse(data=_to_detail(row))


@admin_router.delete(
    "/{article_id}", status_code=204, dependencies=[_admin_write_limit]
)
async def delete_article(
    article_id: uuid.UUID,
    _current_user_id: str = Depends(get_current_user_id),
    use_case: DeleteArticle = Depends(_delete_use_case),
) -> None:
    await use_case.execute(article_id)
