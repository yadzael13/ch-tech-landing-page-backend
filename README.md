# CH-TECH Landing Page — Backend

> API del sitio oficial de CH-TECH, startup de Ingeniería de Software e Inteligencia Artificial.

Este repositorio es el backend, separado de [`ch-tech-landing-page-frontend`](../ch-tech-landing-page-frontend) dentro del ecosistema `ch-tech-ecosystem`. Migrado desde el monorepo original `ch-tech` (PostgreSQL → MySQL, ver `docs/adr/0014-mysql-database-privilege-separation.md`).

CH-TECH diseña, desarrolla e implementa soluciones tecnológicas que ayudan a empresas a automatizar procesos, mejorar su operación y acelerar su crecimiento mediante software e IA. Este repositorio construye esa plataforma siguiendo buenas prácticas de ingeniería de software modernas, incluyendo:

- Arquitectura limpia
- Desarrollo asistido por IA (Claude Code)
- Docker como entorno de desarrollo
- TDD en Backend
- CI/CD
- Security by Design
- Documentación como fuente de verdad

Ver docs/VISION.md para la misión, visión y modelo de negocio completos.

---

# Objetivos

- Presentar a CH-TECH y sus cinco líneas de negocio (Software Engineering, AI & Automation, Digital Solutions, SaaS Products, Technology Consulting).
- Publicar proyectos, casos de estudio y, a futuro, productos SaaS propios.
- Generar leads mediante el formulario de contacto.
- Servir como plantilla para futuros proyectos del equipo.

---

# Stack Tecnológico

## Backend

- FastAPI
- Python
- SQLAlchemy 2.x + Alembic (Clean Architecture, ver `docs/ARCHITECTURE.md`)

## Base de Datos

- MySQL 8.4 (migrado desde PostgreSQL — ver ADR-0014). Dos credenciales
  separadas (`chtech_app` de solo DML, `chtech_migrator` con DDL) para que
  ni la aplicación en ejecución ni un asistente de IA puedan alterar tablas.

## Infraestructura

- Docker
- Docker Compose
- GitHub Actions

---

# Estructura

```
app/                 domain / application / infrastructure / api / core / db / models / schemas
alembic/              migraciones (baseline única, ver docs/DATABASE_MIGRATIONS.md)
scripts/              migration_to_sql.py — genera el DDL como SQL revisable
database/init/        bootstrap de roles MySQL (chtech_app / chtech_migrator)
docs/                 documentación técnica + ADRs
specs/                especificaciones spec-driven (spec/plan/tasks por feature)
docker/               Dockerfiles (backend, nginx)
.github/              CI/CD
```

---

# Desarrollo

```bash
docker compose up --build
```

Repositorio hermano: [`ch-tech-landing-page-frontend`](../ch-tech-landing-page-frontend) — corre de forma independiente (`npm run dev`), apuntando a `NEXT_PUBLIC_API_URL`/`API_URL` hacia este backend. No comparten red de Docker Compose ni base de datos.

---

# Documentación

Toda la documentación vive en la carpeta `docs`.

Antes de implementar una nueva funcionalidad se debe revisar la documentación correspondiente.

---

# Roadmap

Consultar:

docs/ROADMAP.md

---

## License

This project is licensed under the MIT License.
See the LICENSE file for details.