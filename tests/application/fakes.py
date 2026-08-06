"""In-memory ProjectRepository fake — lets use cases be tested without
FastAPI or a real database (ARCHITECTURE.md)."""

import uuid
from dataclasses import replace
from datetime import UTC, datetime

from app.application.ports.article_repository import (
    ArticleInput,
    ArticleWithTechnologies,
)
from app.application.ports.case_study_repository import CaseStudyInput
from app.application.ports.client_repository import ClientInput
from app.application.ports.company_repository import CompanyInput
from app.application.ports.contact_request_repository import ContactRequestInput
from app.application.ports.partner_repository import PartnerInput
from app.application.ports.product_repository import ProductInput
from app.application.ports.project_repository import (
    ProjectFilters,
    ProjectInput,
    ProjectWithTechnologies,
)
from app.application.ports.service_line_repository import ServiceLineInput
from app.application.ports.service_repository import ServiceInput
from app.application.ports.team_member_repository import TeamMemberInput
from app.application.ports.technology_repository import (
    TechnologyFilters,
    TechnologyInput,
)
from app.application.ports.testimonial_repository import TestimonialInput
from app.core.errors import ConflictError
from app.domain.article import Article
from app.domain.case_study import CaseStudy
from app.domain.client import Client
from app.domain.company import Company
from app.domain.contact_request import ContactRequest
from app.domain.enums import ContactStatus
from app.domain.partner import Partner
from app.domain.product import Product
from app.domain.project import Project
from app.domain.refresh_token import RefreshToken
from app.domain.service import Service
from app.domain.service_line import ServiceLine
from app.domain.team_member import TeamMember
from app.domain.technology import Technology
from app.domain.testimonial import Testimonial
from app.domain.user import User
from app.domain.value_objects import Email, Image, MarkdownContent, Slug, Url


class InMemoryProjectRepository:
    def __init__(self, seed: list[ProjectWithTechnologies] | None = None) -> None:
        self._rows: dict[uuid.UUID, ProjectWithTechnologies] = {
            row.project.id: row for row in (seed or [])
        }

    async def list(
        self, filters: ProjectFilters, *, public_only: bool
    ) -> list[ProjectWithTechnologies]:
        rows = list(self._rows.values())
        if public_only:
            rows = [r for r in rows if r.project.visibility.value == "PUBLIC"]
        if filters.technology is not None:
            rows = [
                r
                for r in rows
                if any(t.name == filters.technology for t in r.technologies)
            ]
        if filters.featured is not None:
            rows = [r for r in rows if r.project.featured == filters.featured]
        if filters.status is not None:
            rows = [r for r in rows if r.project.status.value == filters.status]
        if filters.search is not None:
            needle = filters.search.lower()
            rows = [r for r in rows if needle in r.project.title.lower()]

        if filters.sort == "title":
            rows.sort(key=lambda r: r.project.title)
        else:
            rows.sort(key=lambda r: r.project.created_at)

        start = (filters.page - 1) * filters.limit
        return rows[start : start + filters.limit]

    async def get_by_slug(
        self, slug: str, *, public_only: bool
    ) -> ProjectWithTechnologies | None:
        for row in self._rows.values():
            if str(row.project.slug) != slug:
                continue
            if public_only and row.project.visibility.value != "PUBLIC":
                return None
            return row
        return None

    async def get_by_id(self, project_id: uuid.UUID) -> ProjectWithTechnologies | None:
        return self._rows.get(project_id)

    async def create(self, data: ProjectInput) -> ProjectWithTechnologies:
        if any(str(r.project.slug) == data.slug for r in self._rows.values()):
            raise ConflictError("A project with this slug already exists")

        now = datetime.now(UTC)
        project = Project(
            id=uuid.uuid4(),
            slug=Slug(data.slug),
            title=data.title,
            short_description=data.short_description,
            full_description=data.full_description,
            repository_url=Url(data.repository_url) if data.repository_url else None,
            live_demo_url=Url(data.live_demo_url) if data.live_demo_url else None,
            cover_image=Image(data.cover_image) if data.cover_image else None,
            status=data.status,
            visibility=data.visibility,
            featured=data.featured,
            client_id=None,
            started_at=data.started_at,
            finished_at=data.finished_at,
            created_at=now,
            updated_at=now,
        )
        row = ProjectWithTechnologies(project=project, technologies=[])
        self._rows[project.id] = row
        return row

    async def update(
        self, project_id: uuid.UUID, data: ProjectInput
    ) -> ProjectWithTechnologies | None:
        existing = self._rows.get(project_id)
        if existing is None:
            return None

        updated_project = replace(
            existing.project,
            slug=Slug(data.slug),
            title=data.title,
            short_description=data.short_description,
            full_description=data.full_description,
            repository_url=Url(data.repository_url) if data.repository_url else None,
            live_demo_url=Url(data.live_demo_url) if data.live_demo_url else None,
            cover_image=Image(data.cover_image) if data.cover_image else None,
            status=data.status,
            visibility=data.visibility,
            featured=data.featured,
            started_at=data.started_at,
            finished_at=data.finished_at,
            updated_at=datetime.now(UTC),
        )
        row = ProjectWithTechnologies(project=updated_project, technologies=[])
        self._rows[project_id] = row
        return row

    async def delete(self, project_id: uuid.UUID) -> bool:
        return self._rows.pop(project_id, None) is not None


def make_technology(*, name: str = "Python") -> Technology:
    now = datetime.now(UTC)
    return Technology(
        id=uuid.uuid4(),
        name=name,
        category=None,
        icon=None,
        official_url=None,
        created_at=now,
        updated_at=now,
    )


class InMemoryTechnologyRepository:
    def __init__(self, seed: list[Technology] | None = None) -> None:
        self._rows: dict[uuid.UUID, Technology] = {t.id: t for t in (seed or [])}

    async def list(self, filters: TechnologyFilters) -> list[Technology]:
        rows = list(self._rows.values())
        if filters.category is not None:
            rows = [t for t in rows if t.category == filters.category]
        return sorted(rows, key=lambda t: t.name)

    async def get_by_id(self, technology_id: uuid.UUID) -> Technology | None:
        return self._rows.get(technology_id)

    async def create(self, data: TechnologyInput) -> Technology:
        now = datetime.now(UTC)
        technology = Technology(
            id=uuid.uuid4(),
            name=data.name,
            category=data.category,
            icon=Image(data.icon) if data.icon else None,
            official_url=Url(data.official_url) if data.official_url else None,
            created_at=now,
            updated_at=now,
        )
        self._rows[technology.id] = technology
        return technology

    async def update(
        self, technology_id: uuid.UUID, data: TechnologyInput
    ) -> Technology | None:
        existing = self._rows.get(technology_id)
        if existing is None:
            return None
        technology = replace(
            existing,
            name=data.name,
            category=data.category,
            icon=Image(data.icon) if data.icon else None,
            official_url=Url(data.official_url) if data.official_url else None,
            updated_at=datetime.now(UTC),
        )
        self._rows[technology_id] = technology
        return technology

    async def delete(self, technology_id: uuid.UUID) -> bool:
        return self._rows.pop(technology_id, None) is not None


class InMemoryServiceRepository:
    def __init__(self, seed: list[Service] | None = None) -> None:
        self._rows: dict[uuid.UUID, Service] = {s.id: s for s in (seed or [])}

    async def list(self, *, active_only: bool) -> list[Service]:
        rows = list(self._rows.values())
        if active_only:
            rows = [s for s in rows if s.active]
        return sorted(rows, key=lambda s: s.title)

    async def get_by_slug(self, slug: str, *, active_only: bool) -> Service | None:
        for service in self._rows.values():
            if str(service.slug) != slug:
                continue
            if active_only and not service.active:
                return None
            return service
        return None

    async def get_by_id(self, service_id: uuid.UUID) -> Service | None:
        return self._rows.get(service_id)

    async def create(self, data: ServiceInput) -> Service:
        if any(str(s.slug) == data.slug for s in self._rows.values()):
            raise ConflictError("A service with this slug already exists")

        now = datetime.now(UTC)
        service = Service(
            id=uuid.uuid4(),
            service_line_id=None,
            title=data.title,
            slug=Slug(data.slug),
            description=data.description,
            featured=data.featured,
            active=data.active,
            created_at=now,
            updated_at=now,
        )
        self._rows[service.id] = service
        return service

    async def update(self, service_id: uuid.UUID, data: ServiceInput) -> Service | None:
        existing = self._rows.get(service_id)
        if existing is None:
            return None
        if any(
            str(s.slug) == data.slug and s.id != service_id for s in self._rows.values()
        ):
            raise ConflictError("A service with this slug already exists")

        service = replace(
            existing,
            title=data.title,
            slug=Slug(data.slug),
            description=data.description,
            featured=data.featured,
            active=data.active,
            updated_at=datetime.now(UTC),
        )
        self._rows[service_id] = service
        return service

    async def delete(self, service_id: uuid.UUID) -> bool:
        return self._rows.pop(service_id, None) is not None


class InMemoryCaseStudyRepository:
    """public_project_ids stands in for the JOIN a real repository does
    against projects.visibility — this fake just needs to know which
    projects a case study's public visibility depends on."""

    def __init__(
        self,
        seed: list[CaseStudy] | None = None,
        *,
        public_project_ids: set[uuid.UUID] | None = None,
    ) -> None:
        self._rows: dict[uuid.UUID, CaseStudy] = {c.id: c for c in (seed or [])}
        self._public_project_ids = public_project_ids or set()

    def _visible(self, case_study: CaseStudy, *, public_only: bool) -> bool:
        return not public_only or case_study.project_id in self._public_project_ids

    async def list(self, *, public_only: bool) -> list[CaseStudy]:
        rows = [
            c for c in self._rows.values() if self._visible(c, public_only=public_only)
        ]
        return sorted(rows, key=lambda c: c.created_at)

    async def get_by_id(
        self, case_study_id: uuid.UUID, *, public_only: bool
    ) -> CaseStudy | None:
        case_study = self._rows.get(case_study_id)
        if case_study is None or not self._visible(case_study, public_only=public_only):
            return None
        return case_study

    async def create(self, data: CaseStudyInput) -> CaseStudy:
        now = datetime.now(UTC)
        case_study = CaseStudy(
            id=uuid.uuid4(),
            project_id=data.project_id,
            challenge=data.challenge,
            solution=data.solution,
            architecture=data.architecture,
            lessons_learned=data.lessons_learned,
            metrics=data.metrics,
            created_at=now,
            updated_at=now,
        )
        self._rows[case_study.id] = case_study
        return case_study

    async def update(
        self, case_study_id: uuid.UUID, data: CaseStudyInput
    ) -> CaseStudy | None:
        existing = self._rows.get(case_study_id)
        if existing is None:
            return None

        case_study = replace(
            existing,
            project_id=data.project_id,
            challenge=data.challenge,
            solution=data.solution,
            architecture=data.architecture,
            lessons_learned=data.lessons_learned,
            metrics=data.metrics,
            updated_at=datetime.now(UTC),
        )
        self._rows[case_study_id] = case_study
        return case_study

    async def delete(self, case_study_id: uuid.UUID) -> bool:
        return self._rows.pop(case_study_id, None) is not None


class InMemoryArticleRepository:
    def __init__(self, seed: list[ArticleWithTechnologies] | None = None) -> None:
        self._rows: dict[uuid.UUID, ArticleWithTechnologies] = {
            row.article.id: row for row in (seed or [])
        }

    async def list(
        self, *, published_only: bool, page: int, limit: int
    ) -> list[ArticleWithTechnologies]:
        rows = list(self._rows.values())
        if published_only:
            rows = [r for r in rows if r.article.published]
        rows.sort(
            key=lambda r: r.article.published_at or r.article.created_at, reverse=True
        )
        start = (page - 1) * limit
        return rows[start : start + limit]

    async def get_by_slug(
        self, slug: str, *, published_only: bool
    ) -> ArticleWithTechnologies | None:
        for row in self._rows.values():
            if str(row.article.slug) != slug:
                continue
            if published_only and not row.article.published:
                return None
            return row
        return None

    async def get_by_id(self, article_id: uuid.UUID) -> ArticleWithTechnologies | None:
        return self._rows.get(article_id)

    async def create(
        self, data: ArticleInput, *, author_id: uuid.UUID
    ) -> ArticleWithTechnologies:
        if any(str(r.article.slug) == data.slug for r in self._rows.values()):
            raise ConflictError("An article with this slug already exists")

        now = datetime.now(UTC)
        article = Article(
            id=uuid.uuid4(),
            author_id=author_id,
            slug=Slug(data.slug),
            title=data.title,
            summary=data.summary,
            content=MarkdownContent(data.content),
            cover_image=Image(data.cover_image) if data.cover_image else None,
            reading_time=data.reading_time,
            published=data.published,
            published_at=data.published_at,
            created_at=now,
            updated_at=now,
        )
        row = ArticleWithTechnologies(article=article, technologies=[])
        self._rows[article.id] = row
        return row

    async def update(
        self, article_id: uuid.UUID, data: ArticleInput
    ) -> ArticleWithTechnologies | None:
        existing = self._rows.get(article_id)
        if existing is None:
            return None

        updated_article = replace(
            existing.article,
            slug=Slug(data.slug),
            title=data.title,
            summary=data.summary,
            content=MarkdownContent(data.content),
            cover_image=Image(data.cover_image) if data.cover_image else None,
            reading_time=data.reading_time,
            published=data.published,
            published_at=data.published_at,
            updated_at=datetime.now(UTC),
        )
        row = ArticleWithTechnologies(article=updated_article, technologies=[])
        self._rows[article_id] = row
        return row

    async def delete(self, article_id: uuid.UUID) -> bool:
        return self._rows.pop(article_id, None) is not None


class InMemoryContactRequestRepository:
    def __init__(self) -> None:
        self.created: list[ContactRequest] = []

    async def create(self, data: ContactRequestInput) -> ContactRequest:
        contact_request = ContactRequest(
            id=uuid.uuid4(),
            name=data.name,
            email=Email(data.email),
            company=data.company,
            subject=data.subject,
            message=data.message,
            interested_service_line_id=None,
            source=None,
            status=ContactStatus.NEW,
            created_at=datetime.now(UTC),
        )
        self.created.append(contact_request)
        return contact_request


class InMemoryUserRepository:
    def __init__(self, seed: list[User] | None = None) -> None:
        self._rows: dict[uuid.UUID, User] = {u.id: u for u in (seed or [])}

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._rows.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        for user in self._rows.values():
            if str(user.email) == email:
                return user
        return None

    async def record_login(self, user_id: uuid.UUID, *, at: datetime) -> None:
        user = self._rows.get(user_id)
        if user is not None:
            self._rows[user_id] = replace(user, last_login=at)


class InMemoryRefreshTokenRepository:
    def __init__(self, seed: list[RefreshToken] | None = None) -> None:
        self._rows: dict[uuid.UUID, RefreshToken] = {t.id: t for t in (seed or [])}

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        issued_at: datetime,
        expires_at: datetime,
        user_agent: str | None,
        ip_address: str | None,
    ) -> RefreshToken:
        token = RefreshToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            issued_at=issued_at,
            expires_at=expires_at,
            revoked_at=None,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self._rows[token.id] = token
        return token

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        for token in self._rows.values():
            if token.token_hash == token_hash:
                return token
        return None

    async def save(self, token: RefreshToken) -> None:
        self._rows[token.id] = token

    async def revoke_if_active(
        self, token_hash: str, *, at: datetime
    ) -> RefreshToken | None:
        for token in self._rows.values():
            if token.token_hash == token_hash and token.is_active(at=at):
                token.revoke(at=at)
                return token
        return None

    async def purge_older_than(self, cutoff: datetime) -> int:
        to_delete = [
            token_id
            for token_id, token in self._rows.items()
            if token.expires_at < cutoff
            or (token.revoked_at is not None and token.revoked_at < cutoff)
        ]
        for token_id in to_delete:
            del self._rows[token_id]
        return len(to_delete)


class InMemoryServiceLineRepository:
    def __init__(self, seed: list[ServiceLine] | None = None) -> None:
        self._rows: dict[uuid.UUID, ServiceLine] = {s.id: s for s in (seed or [])}

    async def list(self) -> list[ServiceLine]:
        return sorted(self._rows.values(), key=lambda s: s.display_order)

    async def get_by_slug(self, slug: str) -> ServiceLine | None:
        for line in self._rows.values():
            if str(line.slug) == slug:
                return line
        return None

    async def create(self, data: ServiceLineInput) -> ServiceLine:
        if any(str(s.slug) == data.slug for s in self._rows.values()):
            raise ConflictError("A service line with this slug already exists")

        now = datetime.now(UTC)
        line = ServiceLine(
            id=uuid.uuid4(),
            slug=Slug(data.slug),
            name=data.name,
            description=data.description,
            icon=Image(data.icon) if data.icon else None,
            display_order=data.display_order,
            created_at=now,
            updated_at=now,
        )
        self._rows[line.id] = line
        return line

    async def update(
        self, service_line_id: uuid.UUID, data: ServiceLineInput
    ) -> ServiceLine | None:
        existing = self._rows.get(service_line_id)
        if existing is None:
            return None
        if any(
            str(s.slug) == data.slug and s.id != service_line_id
            for s in self._rows.values()
        ):
            raise ConflictError("A service line with this slug already exists")

        line = replace(
            existing,
            slug=Slug(data.slug),
            name=data.name,
            description=data.description,
            icon=Image(data.icon) if data.icon else None,
            display_order=data.display_order,
            updated_at=datetime.now(UTC),
        )
        self._rows[service_line_id] = line
        return line

    async def delete(self, service_line_id: uuid.UUID) -> bool:
        return self._rows.pop(service_line_id, None) is not None


class InMemoryClientRepository:
    def __init__(self, seed: list[Client] | None = None) -> None:
        self._rows: dict[uuid.UUID, Client] = {c.id: c for c in (seed or [])}

    async def list(self) -> list[Client]:
        return sorted(self._rows.values(), key=lambda c: c.name)

    async def get_by_id(self, client_id: uuid.UUID) -> Client | None:
        return self._rows.get(client_id)

    async def create(self, data: ClientInput) -> Client:
        now = datetime.now(UTC)
        client = Client(
            id=uuid.uuid4(),
            name=data.name,
            logo=Image(data.logo) if data.logo else None,
            industry=data.industry,
            website_url=Url(data.website_url) if data.website_url else None,
            created_at=now,
            updated_at=now,
        )
        self._rows[client.id] = client
        return client

    async def update(self, client_id: uuid.UUID, data: ClientInput) -> Client | None:
        existing = self._rows.get(client_id)
        if existing is None:
            return None
        client = replace(
            existing,
            name=data.name,
            logo=Image(data.logo) if data.logo else None,
            industry=data.industry,
            website_url=Url(data.website_url) if data.website_url else None,
            updated_at=datetime.now(UTC),
        )
        self._rows[client_id] = client
        return client

    async def delete(self, client_id: uuid.UUID) -> bool:
        return self._rows.pop(client_id, None) is not None


class InMemoryPartnerRepository:
    def __init__(self, seed: list[Partner] | None = None) -> None:
        self._rows: dict[uuid.UUID, Partner] = {p.id: p for p in (seed or [])}

    async def list(self) -> list[Partner]:
        return sorted(self._rows.values(), key=lambda p: p.name)

    async def get_by_id(self, partner_id: uuid.UUID) -> Partner | None:
        return self._rows.get(partner_id)

    async def create(self, data: PartnerInput) -> Partner:
        now = datetime.now(UTC)
        partner = Partner(
            id=uuid.uuid4(),
            name=data.name,
            logo=Image(data.logo) if data.logo else None,
            partnership_type=data.partnership_type,
            website_url=Url(data.website_url) if data.website_url else None,
            created_at=now,
            updated_at=now,
        )
        self._rows[partner.id] = partner
        return partner

    async def update(self, partner_id: uuid.UUID, data: PartnerInput) -> Partner | None:
        existing = self._rows.get(partner_id)
        if existing is None:
            return None
        partner = replace(
            existing,
            name=data.name,
            logo=Image(data.logo) if data.logo else None,
            partnership_type=data.partnership_type,
            website_url=Url(data.website_url) if data.website_url else None,
            updated_at=datetime.now(UTC),
        )
        self._rows[partner_id] = partner
        return partner

    async def delete(self, partner_id: uuid.UUID) -> bool:
        return self._rows.pop(partner_id, None) is not None


class InMemoryTestimonialRepository:
    def __init__(self, seed: list[Testimonial] | None = None) -> None:
        self._rows: dict[uuid.UUID, Testimonial] = {t.id: t for t in (seed or [])}

    async def list(self) -> list[Testimonial]:
        return sorted(self._rows.values(), key=lambda t: t.created_at)

    async def create(self, data: TestimonialInput) -> Testimonial:
        now = datetime.now(UTC)
        testimonial = Testimonial(
            id=uuid.uuid4(),
            author_name=data.author_name,
            author_role=data.author_role,
            client_id=data.client_id,
            project_id=data.project_id,
            content=data.content,
            rating=data.rating,
            featured=data.featured,
            created_at=now,
            updated_at=now,
        )
        self._rows[testimonial.id] = testimonial
        return testimonial

    async def update(
        self, testimonial_id: uuid.UUID, data: TestimonialInput
    ) -> Testimonial | None:
        existing = self._rows.get(testimonial_id)
        if existing is None:
            return None
        testimonial = replace(
            existing,
            author_name=data.author_name,
            author_role=data.author_role,
            client_id=data.client_id,
            project_id=data.project_id,
            content=data.content,
            rating=data.rating,
            featured=data.featured,
            updated_at=datetime.now(UTC),
        )
        self._rows[testimonial_id] = testimonial
        return testimonial

    async def delete(self, testimonial_id: uuid.UUID) -> bool:
        return self._rows.pop(testimonial_id, None) is not None


class InMemoryProductRepository:
    def __init__(self, seed: list[Product] | None = None) -> None:
        self._rows: dict[uuid.UUID, Product] = {p.id: p for p in (seed or [])}

    async def list(self) -> list[Product]:
        return sorted(self._rows.values(), key=lambda p: p.name)

    async def get_by_slug(self, slug: str) -> Product | None:
        for product in self._rows.values():
            if str(product.slug) == slug:
                return product
        return None

    async def create(self, data: ProductInput) -> Product:
        if any(str(p.slug) == data.slug for p in self._rows.values()):
            raise ConflictError("A product with this slug already exists")

        now = datetime.now(UTC)
        product = Product(
            id=uuid.uuid4(),
            slug=Slug(data.slug),
            name=data.name,
            short_description=data.short_description,
            full_description=data.full_description,
            status=data.status,
            url=Url(data.url) if data.url else None,
            logo=Image(data.logo) if data.logo else None,
            featured=data.featured,
            created_at=now,
            updated_at=now,
        )
        self._rows[product.id] = product
        return product

    async def update(self, product_id: uuid.UUID, data: ProductInput) -> Product | None:
        existing = self._rows.get(product_id)
        if existing is None:
            return None
        if any(
            str(p.slug) == data.slug and p.id != product_id for p in self._rows.values()
        ):
            raise ConflictError("A product with this slug already exists")

        product = replace(
            existing,
            slug=Slug(data.slug),
            name=data.name,
            short_description=data.short_description,
            full_description=data.full_description,
            status=data.status,
            url=Url(data.url) if data.url else None,
            logo=Image(data.logo) if data.logo else None,
            featured=data.featured,
            updated_at=datetime.now(UTC),
        )
        self._rows[product_id] = product
        return product

    async def delete(self, product_id: uuid.UUID) -> bool:
        return self._rows.pop(product_id, None) is not None


class InMemoryTeamMemberRepository:
    def __init__(self, seed: list[TeamMember] | None = None) -> None:
        self._rows: dict[uuid.UUID, TeamMember] = {m.id: m for m in (seed or [])}

    async def list(self, *, active_only: bool) -> list[TeamMember]:
        rows = list(self._rows.values())
        if active_only:
            rows = [m for m in rows if m.active]
        return sorted(rows, key=lambda m: m.display_order)

    async def get_by_id(
        self, team_member_id: uuid.UUID, *, active_only: bool
    ) -> TeamMember | None:
        member = self._rows.get(team_member_id)
        if member is None:
            return None
        if active_only and not member.active:
            return None
        return member

    async def create(self, data: TeamMemberInput) -> TeamMember:
        now = datetime.now(UTC)
        member = TeamMember(
            id=uuid.uuid4(),
            user_id=data.user_id,
            name=data.name,
            role=data.role,
            bio=data.bio,
            photo=Image(data.photo) if data.photo else None,
            linkedin_url=Url(data.linkedin_url) if data.linkedin_url else None,
            github_url=Url(data.github_url) if data.github_url else None,
            display_order=data.display_order,
            active=data.active,
            created_at=now,
            updated_at=now,
        )
        self._rows[member.id] = member
        return member

    async def update(
        self, team_member_id: uuid.UUID, data: TeamMemberInput
    ) -> TeamMember | None:
        existing = self._rows.get(team_member_id)
        if existing is None:
            return None
        member = replace(
            existing,
            user_id=data.user_id,
            name=data.name,
            role=data.role,
            bio=data.bio,
            photo=Image(data.photo) if data.photo else None,
            linkedin_url=Url(data.linkedin_url) if data.linkedin_url else None,
            github_url=Url(data.github_url) if data.github_url else None,
            display_order=data.display_order,
            active=data.active,
            updated_at=datetime.now(UTC),
        )
        self._rows[team_member_id] = member
        return member

    async def delete(self, team_member_id: uuid.UUID) -> bool:
        return self._rows.pop(team_member_id, None) is not None


class InMemoryCompanyRepository:
    def __init__(self, seed: Company | None = None) -> None:
        self._row: Company | None = seed

    async def get(self) -> Company | None:
        return self._row

    async def update(self, data: CompanyInput) -> Company:
        now = datetime.now(UTC)
        self._row = Company(
            id=self._row.id if self._row is not None else uuid.uuid4(),
            legal_name=data.legal_name,
            display_name=data.display_name,
            tagline=data.tagline,
            mission=data.mission,
            vision=data.vision,
            email=Email(data.email) if data.email else None,
            phone=data.phone,
            address=data.address,
            social_links=data.social_links,
            created_at=self._row.created_at if self._row is not None else now,
            updated_at=now,
        )
        return self._row
