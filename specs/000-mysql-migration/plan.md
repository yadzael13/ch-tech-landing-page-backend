# Plan 000: Migración a MySQL y separación de repos (backend)

## Enfoque técnico

No se reescribe el stack (FastAPI + SQLAlchemy 2.x async + Alembic + Clean
Architecture se mantienen intactos — decisión ya evaluada y documentada en
el plan de migración completo). El cambio es de capa de datos y de
estructura de repositorio, no de arquitectura de aplicación.

### 1. Capa de conexión

`app/db/types.py` — nuevo `GUID` (`TypeDecorator` sobre `CHAR(36)`)
reemplaza `sqlalchemy.dialects.postgresql.UUID` en todos los modelos, sin
cambiar el tipado Python (`Mapped[uuid.UUID]`). `app/core/config.py` gana
`migration_database_url`, separado de `database_url`.

### 2. Separación de privilegios (ver ADR-0014)

`database/init/01-create-roles.sh` crea `chtech_app` (DML) y
`chtech_migrator` (DDL+DML) en desarrollo; `.github/workflows/ci.yml` los
bootstrapea explícitamente en CI; producción (RDS) los crea como paso
manual único (`docs/DEPLOYMENT.md`). `alembic/env.py` lee
`migration_database_url` exclusivamente.

### 3. Modelos

`JSONB` → `JSON` (`case_study.py`, `company.py`). Índice funcional
`lower(email)` → columna generada `email_lower` (`Computed(...,
persisted=True)`) en `user.py`. Índice trigram de `projects.title` → índice
B-tree normal.

### 4. Repositorios

`refresh_token_repository.py`: los dos métodos que usaban `RETURNING`
(sin equivalente en MySQL) se reescriben como SELECT-then-UPDATE/DELETE,
con `SELECT ... FOR UPDATE` en `revoke_if_active()` para no perder
atomicidad frente a una doble-revocación concurrente.

### 5. Migración baseline

Las 21 migraciones Postgres-específicas se reemplazan por una única
baseline (`alembic/versions/0001_baseline_mysql_schema.py`), generada con
`alembic revision --autogenerate` contra una MySQL real vacía (no escrita a
mano) — así queda garantizado sin drift por construcción. Justificado
porque el alcance es solo-estructura (sin datos reales que replayar).

### 6. Verificación

Contra un contenedor MySQL 8.4 real (no mockeado): roundtrip completo de
migración, seed, y un test dedicado (`tests/test_db_privilege_boundary.py`)
que prueba la separación de privilegios conectándose directamente con cada
credencial.

## Riesgos aceptados

- Los tests (`tests/conftest.py`) usan `chtech_migrator` para poder crear y
  destruir su base de datos efímera — excepción intencional y documentada
  al límite DML/DDL, acotada a bases de datos de test.
- Collation `utf8mb4_0900_as_cs` elegida para preservar semántica
  case-sensitive de Postgres en `slug`/`name`/`token_hash`; distinto del
  default de MySQL (`utf8mb4_0900_ai_ci`).
