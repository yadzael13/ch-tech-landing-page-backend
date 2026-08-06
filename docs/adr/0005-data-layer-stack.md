# ADR-0005

## Título

Adoptar SQLAlchemy 2.x, Alembic y Pydantic v2 como capa de datos del backend.

## Estado

Aceptado

## Fecha

2026-08-01

---

## Contexto

CH-TECH necesita un ORM y una herramienta de migraciones para su base de datos relacional, y un mecanismo de validación de datos para FastAPI. El esquema debe evolucionar de forma versionada y auditable (ver DATABASE_VERSIONING.md).

> **Actualización (migración a MySQL):** el motor de base de datos original
> era PostgreSQL; el proyecto migró a MySQL 8.4 al separar este repositorio
> del monorepo original (ver ADR-0014). La decisión de esta ADR —
> SQLAlchemy 2.x + Alembic + Pydantic v2 — no cambia: SQLAlchemy/Alembic son
> agnósticos de motor por diseño, solo cambió el dialecto (`postgresql+asyncpg://`
> → `mysql+aiomysql://`) y algunos tipos dialecto-específicos (ver
> DATABASE_SCHEMA.md). No se reescribe el resto de esta ADR porque documenta
> una decisión histórica correcta en su momento.

---

## Decisión

Se utiliza SQLAlchemy 2.x como ORM, Alembic para migraciones versionadas, y Pydantic v2 para validación y serialización en los endpoints de FastAPI.

---

## Alternativas

- SQLModel (más simple, pero menos maduro y acopla ORM con schemas de API)
- Tortoise ORM (async-first, ecosistema más pequeño)
- Raw SQL con el driver del motor (máximo control, mayor costo de mantenimiento)

---

## Consecuencias

### Positivas

- Ecosistema maduro y ampliamente documentado.
- Integración nativa de Alembic con SQLAlchemy.
- Pydantic v2 es el estándar de facto en FastAPI.

### Negativas

- SQLAlchemy 2.x tiene una curva de aprendizaje para su API moderna (2.0 style).
- Mantener sincronizados modelos SQLAlchemy y schemas Pydantic requiere disciplina (ver API.md, sección OpenAPI).

---

## Referencias

https://docs.sqlalchemy.org/

https://alembic.sqlalchemy.org/

https://docs.pydantic.dev/
