# CLAUDE.md

Guía para Claude Code (o cualquier asistente de IA) trabajando en este repositorio — el backend de CH-TECH, separado del monorepo original `ch-tech`.

## Antes de nada

Lee `docs/AI_GUIDELINES.md` — es el conjunto de reglas de flujo de trabajo (branching, commits, TDD, alcance de cambios) que este repositorio espera de cualquier agente de IA. Esta guía no las repite; las complementa con contexto específico de este repo.

## Regla no negociable: privilegios de base de datos

La aplicación en ejecución se conecta con `chtech_app`, una credencial MySQL sin privilegios `CREATE`/`ALTER`/`DROP` — MySQL rechaza cualquier intento de DDL por esa vía, sin excepción (ver `docs/adr/0014-mysql-database-privilege-separation.md`). Si una tarea requiere cambiar el esquema:

1. Escribir una migración Alembic nueva (nunca editar una existente).
2. Generar el SQL revisable: `python scripts/migration_to_sql.py`.
3. Aplicarla con la credencial `chtech_migrator` (`alembic upgrade head`), nunca ejecutando SQL manual.

Nunca proponer ni ejecutar `ALTER TABLE`/`DROP TABLE`/`CREATE TABLE` fuera de ese flujo.

## Stack y arquitectura

FastAPI + SQLAlchemy 2.x (async) + Alembic + MySQL 8.4, Clean Architecture (`domain` → `application` → `infrastructure` → `api`, ver `docs/ARCHITECTURE.md`). TDD obligatorio (`docs/TESTING.md`). Ver `docs/DATA_MODEL.md` y `docs/DATABASE_SCHEMA.md` para el modelo de datos completo.

## Desarrollo guiado por especificaciones (spec-driven)

Para cambios no triviales, antes de escribir código: crear `specs/NNN-nombre-feature/` con `spec.md` (qué y por qué — requisitos, criterios de aceptación), `plan.md` (cómo — enfoque técnico) y `tasks.md` (checklist ordenado, TDD-first). Ver `specs/000-mysql-migration/` como ejemplo real. Esto se apoya en el Plan Mode nativo de Claude Code — no requiere herramientas adicionales.

## Comandos frecuentes

```bash
docker compose up --build          # entorno completo (backend + MySQL + Redis)
docker compose exec backend pytest --cov
docker compose exec backend alembic upgrade head
python scripts/migration_to_sql.py # DDL revisable antes de aplicar una migración
```

## Repositorio hermano

El frontend vive en `../ch-tech-landing-page-frontend`, repo independiente. Este backend nunca debe asumir que el frontend comparte red de Docker, base de datos o proceso — la única superficie de contacto es la API HTTP versionada (`docs/API.md`).
