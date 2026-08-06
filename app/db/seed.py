import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models import Company, TeamMember, Technology, User

# Reference catalog only (icon/official_url left for an admin to fill in
# later); DATABASE_MIGRATIONS.md reserves migrations for structure, not data.
TECHNOLOGY_CATALOG = [
    ("Python", "Language"),
    ("FastAPI", "Framework"),
    ("Next.js", "Framework"),
    ("Docker", "Infra"),
    ("MySQL", "Database"),
]


async def seed_admin_user(session: AsyncSession) -> None:
    settings = get_settings()
    # Matches the normalization the Email value object applies to every
    # other write path (domain/value_objects.py) — this is the one place
    # that constructs a User without going through it.
    admin_email = settings.seed_admin_email.strip().lower()
    existing = await session.execute(select(User).where(User.email == admin_email))
    if existing.scalar_one_or_none() is not None:
        return

    session.add(
        User(
            name=settings.seed_admin_name,
            email=admin_email,
            password_hash=hash_password(settings.seed_admin_password),
        )
    )


async def seed_technologies(session: AsyncSession) -> None:
    for name, category in TECHNOLOGY_CATALOG:
        existing = await session.execute(
            select(Technology).where(Technology.name == name)
        )
        if existing.scalar_one_or_none() is not None:
            continue
        session.add(Technology(name=name, category=category))


async def seed_company(session: AsyncSession) -> None:
    """Company is a singleton (API.md — no POST/DELETE); this is its only
    creation path. VISION.md is the source for these baseline values —
    an admin can edit them afterward via PUT /admin/company."""
    existing = await session.execute(select(Company).limit(1))
    if existing.scalar_one_or_none() is not None:
        return

    session.add(
        Company(
            legal_name="CH-TECH",
            display_name="CH-TECH",
            tagline=(
                "Construimos software moderno, automatizaciones con IA y "
                "productos digitales escalables para empresas que quieren crecer."
            ),
            mission=(
                "Diseñar, desarrollar e implementar soluciones tecnológicas que "
                "ayuden a empresas a automatizar procesos, mejorar su operación "
                "y acelerar su crecimiento mediante software e inteligencia "
                "artificial."
            ),
            vision=(
                "Convertir a CH-TECH en una empresa capaz de combinar Desarrollo "
                "de Software, Inteligencia Artificial, Automatización, Productos "
                "SaaS, Consultoría Tecnológica e Investigación e Innovación bajo "
                "una misma marca."
            ),
        )
    )


async def seed_team(session: AsyncSession) -> None:
    """Founder as the first TeamMember (VISION.md, DATA_MODEL.md), linked
    to the seeded admin login since that's the account with panel access.
    Depends on seed_admin_user having already run in this session."""
    existing = await session.execute(
        select(TeamMember).where(TeamMember.name == "Yadzael Chalico")
    )
    if existing.scalar_one_or_none() is not None:
        return

    settings = get_settings()
    admin = await session.execute(
        select(User).where(User.email == settings.seed_admin_email.strip().lower())
    )
    admin_user = admin.scalar_one()

    session.add(
        TeamMember(
            user_id=admin_user.id,
            name="Yadzael Chalico",
            role="Founder & Lead Software Engineer",
            bio=(
                "Fundador de CH-TECH. Diseña y construye arquitecturas "
                "escalables, automatizaciones con IA y productos digitales "
                "con prácticas de ingeniería moderna, de principio a fin."
            ),
            display_order=0,
            active=True,
        )
    )


async def main() -> None:
    async with async_session_factory() as session:
        await seed_admin_user(session)
        await seed_technologies(session)
        await seed_company(session)
        await seed_team(session)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
