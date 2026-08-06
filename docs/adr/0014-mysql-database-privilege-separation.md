# ADR-0014

## Título

Migrar de PostgreSQL a MySQL y separar los privilegios de base de datos en dos credenciales (`chtech_app` / `chtech_migrator`).

## Estado

Aceptado

## Fecha

2026-08-06

---

## Contexto

Este repositorio nace de una migración: el backend se separó del monorepo
`ch-tech` original hacia `ch-tech-landing-page-backend`, y en el proceso la
base de datos pasó de PostgreSQL (ADR-0005) a MySQL 8.4. Ver
DATABASE_SCHEMA.md para el detalle de los tipos/índices que cambiaron
(UUID→CHAR(36), JSONB→JSON, índice trigram→B-tree, etc.).

Independiente del cambio de motor, surgió un requisito nuevo: **ningún
asistente de IA — ni el que edita el código de este repo (Claude Code, ver
AI_GUIDELINES.md), ni una futura feature de IA en el producto — debe poder
modificar o alterar la estructura de las tablas**, ni desde el backend ni
desde el frontend. Antes de esta ADR existía un único usuario de base de
datos (`chtech`, en Postgres) con privilegios totales, usado tanto por la
aplicación en ejecución como por las migraciones de Alembic. Una regla
escrita en un `.md` (como las de AI_GUIDELINES.md) es una convención, no una
garantía: nada impedía técnicamente que una consulta con privilegios de
esquema alterara una tabla.

---

## Decisión

Se crean dos credenciales MySQL distintas, con privilegios disjuntos:

- **`chtech_app`** — únicamente `SELECT, INSERT, UPDATE, DELETE` sobre el
  esquema `chtech`. Es la credencial que usa la aplicación FastAPI en
  ejecución (`DATABASE_URL`, `app/db/session.py`). No tiene
  `CREATE`/`ALTER`/`DROP`/`INDEX` — si en el futuro se agrega una feature de
  IA en el producto, debe reutilizar esta misma credencial (o una futura
  `chtech_ai_ro` de solo `SELECT`, aún más restringida), nunca una con
  privilegios de esquema.
- **`chtech_migrator`** — privilegios DDL además de DML. Usada
  exclusivamente por Alembic (`MIGRATION_DATABASE_URL`,
  `alembic/env.py`), y solo como paso explícito de CI/manual — nunca dentro
  del `CMD` del contenedor en producción (patrón que el proyecto ya seguía
  desde ADR-0010/ADR-0011, y que ahora además es el límite de privilegios).

El bootstrap de ambos usuarios vive en `database/init/01-create-roles.sh`
(auto-ejecutado por la imagen oficial de MySQL en desarrollo vía
`docker-entrypoint-initdb.d`) y se replica explícitamente en CI
(`.github/workflows/ci.yml`, paso "Bootstrap DB roles"). En producción
(Amazon RDS, sin ese hook de init) es un paso manual de una sola vez,
documentado en DEPLOYMENT.md.

El script `scripts/migration_to_sql.py` (`alembic upgrade head --sql`)
permite revisar el DDL generado como texto plano antes de aplicarlo,
reforzando que el cambio de esquema es siempre una acción explícita y
auditada, nunca un efecto secundario de una consulta de la aplicación.

La garantía se verifica automáticamente en CI y localmente: un test conecta
directamente como `chtech_app` e intenta un `ALTER TABLE`, y confirma que
MySQL lo rechaza con el error `1142 (42000)` (ver
`tests/test_db_privilege_boundary.py`).

---

## Alternativas

- **Confiar solo en la convención documentada (AI_GUIDELINES.md,
  PROJECT_RULES.md)**: es lo que había antes. No aporta ninguna garantía
  técnica — depende de que humanos y agentes de IA sigan la regla siempre,
  sin excepción.
- **Row-Level Security / vistas restringidas**: resuelve un problema
  distinto (qué filas puede leer/escribir un usuario), no DDL. No aplica
  aquí.
- **Un único usuario con `REVOKE` selectivo aplicado manualmente antes de
  cada deploy**: fràgil y con estado implícito (fácil de olvidar re-aplicar
  el `REVOKE` después de una migración manual de emergencia). Dos usuarios
  con `GRANT`s fijos es más simple de razonar y auditar.

---

## Consecuencias

### Positivas

- La restricción "la IA no puede alterar tablas" queda garantizada por
  MySQL mismo (error de permisos), no solo por una instrucción en un
  archivo de texto que un agente podría ignorar o malinterpretar.
- Separa con claridad "cambiar el esquema" (evento raro, revisado en PR, vía
  Alembic) de "leer/escribir datos" (constante, es la operación normal de
  la app).
- El mismo diseño sirve de base para una futura feature de IA en producto:
  ya existe la credencial de mínimo privilegio a la que debería conectarse.

### Negativas

- Dos credenciales que rotar/gestionar en vez de una, tanto en desarrollo
  (`.env`) como en CI (secrets) y producción (gestor de secretos de RDS).
- El bootstrap de roles no tiene un hook nativo en RDS como
  `docker-entrypoint-initdb.d` — requiere un paso manual documentado (ver
  DEPLOYMENT.md) la primera vez que se aprovisiona la base de datos.
- Los tests (`tests/conftest.py`) necesitan la credencial `chtech_migrator`
  para crear/destruir la base de datos de pruebas en cada corrida — una
  excepción intencional y documentada al límite DML/DDL, acotada a bases de
  datos desechables de test, nunca a producción.

---

## Referencias

https://dev.mysql.com/doc/refman/8.4/en/grant.html

DATABASE_SCHEMA.md — detalle del cambio de motor Postgres → MySQL.
