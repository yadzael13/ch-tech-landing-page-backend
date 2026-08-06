# Database Schema

## Objetivo

Este documento define el esquema físico de la base de datos de CH-TECH.

Representa cómo se almacenarán las entidades del dominio en MySQL.

No describe la implementación del ORM.

Las migraciones serán gestionadas mediante Alembic.

---

# Información General

Motor

- MySQL 8.4 (mínimo 8.0.16, requerido para `CHECK` nativo)
- Charset/collation: `utf8mb4` / `utf8mb4_0900_as_cs` (sensible a mayúsculas y
  acentos, para preservar la misma semántica de unicidad que tenía Postgres
  por defecto — ver ADR-0014)

Versionado

- Alembic

ORM

- SQLAlchemy 2.x

Convenciones

- Todas las tablas utilizan UUID como llave primaria, generado en Python
  (`uuid.uuid4()`) y almacenado como `CHAR(36)` (tipo `GUID` en
  `app/db/types.py` — MySQL no tiene un tipo UUID nativo).
- Los nombres de tablas están en plural.
- Los nombres de columnas utilizan snake_case.
- Todas las tablas incluyen auditoría.
- Todas las fechas se almacenan en UTC, en columnas `DATETIME(6)` (no
  `TIMESTAMP`: evita la conversión implícita a UTC y el límite de 2038 de
  `TIMESTAMP` en MySQL — la app ya normaliza a UTC en Python antes de
  escribir). El `(6)` (microsegundos) es deliberado: el `DATETIME` de MySQL
  por defecto solo guarda segundos completos (`fsp=0`), a diferencia del
  `timestamp` de Postgres, que es de precisión de microsegundo por defecto —
  sin esto se perdería precisión real frente al comportamiento original
  (`app/db/types.py::UTCDateTime`).
- No se utiliza borrado físico cuando sea posible; preferir soft delete cuando aplique.

> **Nota de migración:** este esquema originalmente corría en PostgreSQL
> (ver ADR-0005). Se migró a MySQL al separar este repositorio del monorepo
> `ch-tech` original — ver ADR-0014 para el diseño de privilegios
> (`chtech_app` / `chtech_migrator`) y las notas de compatibilidad por tabla
> marcadas "Postgres → MySQL" más abajo.

---

# Convenciones de Auditoría

Las siguientes columnas estarán presentes en la mayoría de las tablas.

| Columna | Tipo | Descripción |
|----------|------|-------------|
| id | UUID | Identificador único |
| created_at | TIMESTAMP | Fecha de creación |
| updated_at | TIMESTAMP | Fecha de actualización |

Algunas entidades incluirán además:

| Columna | Tipo |
|----------|------|
| deleted_at | TIMESTAMP NULL |

---

# Tablas

## users

Descripción

Administradores del sistema.

Columnas

| Columna | Tipo | Restricciones |
|----------|------|---------------|
| id | UUID | PK |
| name | VARCHAR(150) | NOT NULL |
| email | VARCHAR(255) | UNIQUE |
| email_lower | VARCHAR(255) | NOT NULL, `GENERATED ALWAYS AS (LOWER(email)) STORED` |
| password_hash | TEXT | NOT NULL |
| role | VARCHAR(50) | NOT NULL, CHECK (role IN ('ADMIN')) |
| is_active | BOOLEAN | DEFAULT TRUE |
| last_login | TIMESTAMP | NULL |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

Índices

- email
- email_lower — UNIQUE, case-insensitive (defensa en profundidad: el value object `Email` normaliza a minúsculas antes de escribir, este índice lo respalda a nivel de BD para cualquier ruta de escritura que lo omita). **Postgres → MySQL:** Postgres usaba un índice funcional (`UNIQUE INDEX ... (lower(email))`) directamente sobre una expresión; MySQL no soporta indexar una expresión arbitraria así, por lo que `email_lower` es ahora una columna generada y persistida (`GENERATED ALWAYS AS ... STORED`) con un índice UNIQUE normal encima — mismo efecto, mecanismo distinto.

El `CHECK` de `role` debe extenderse en la misma migración en que se agregue un nuevo valor a `UserRole` en `DATA_MODEL.md` — ambos deben cambiar juntos.

---

## companies — NUEVO (CH-TECH V2)

Descripción

Perfil público de la empresa. Tabla de un único registro (singleton) — no se expone `POST` ni `DELETE` en la API.

| Columna | Tipo | Restricciones |
|----------|------|---------------|
| id | UUID | PK |
| legal_name | VARCHAR(255) | NOT NULL |
| display_name | VARCHAR(150) | NOT NULL |
| tagline | VARCHAR(255) | NULL |
| mission | TEXT | NULL |
| vision | TEXT | NULL |
| email | VARCHAR(255) | NULL |
| phone | VARCHAR(50) | NULL |
| address | TEXT | NULL |
| social_links | JSON | NULL — **Postgres → MySQL:** era `JSONB`; MySQL usa `JSON` nativo (5.7.8+), sin operadores tipo `@>`/`?` de JSONB, que no se usaban en el código de la app. |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

---

## team_members — NUEVO (CH-TECH V2)

Descripción

Personas del equipo mostradas públicamente.

| Columna | Tipo | Restricciones |
|----------|------|---------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NULL |
| name | VARCHAR(150) | NOT NULL |
| role | VARCHAR(150) | NOT NULL |
| bio | TEXT | NULL |
| photo | TEXT | NULL |
| linkedin_url | TEXT | NULL |
| github_url | TEXT | NULL |
| display_order | INTEGER | DEFAULT 0 |
| active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

Índices

- user_id
- active

---

## service_lines — NUEVO (CH-TECH V2)

Descripción

Las cinco líneas de negocio de CH-TECH.

| Columna | Tipo | Restricciones |
|----------|------|---------------|
| id | UUID | PK |
| slug | VARCHAR(150) | UNIQUE, NOT NULL |
| name | VARCHAR(150) | NOT NULL |
| description | TEXT | NULL |
| icon | TEXT | NULL |
| display_order | INTEGER | DEFAULT 0 |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

Índices

- slug

---

## projects

Descripción

Proyectos desarrollados por CH-TECH.

Columnas

| Columna | Tipo |
|----------|------|
| id | UUID |
| slug | VARCHAR(150) |
| title | VARCHAR(255) |
| short_description | TEXT |
| full_description | TEXT |
| repository_url | TEXT |
| live_demo_url | TEXT |
| cover_image | TEXT |
| status | VARCHAR(50) |
| visibility | VARCHAR(50) |
| featured | BOOLEAN |
| client_id | UUID — NUEVO (CH-TECH V2), FK → clients.id, NULL |
| started_at | DATE |
| finished_at | DATE |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

Índices

- slug
- featured
- status
- client_id — NUEVO (CH-TECH V2)
- title (B-tree) — soporta `GET /projects?search=`. **Postgres → MySQL:** el índice original era GIN con la extensión `pg_trgm` (trigram), sin equivalente en MySQL; se reemplazó por un índice B-tree normal. El catálogo de proyectos es pequeño (contenido de un landing page), así que no hace falta un índice especializado para el `LIKE '%term%'` con comodín inicial — el trigram original era una optimización, no una funcionalidad distinta.

---

## technologies

Descripción

Tecnologías utilizadas en proyectos y artículos.

| Columna | Tipo |
|----------|------|
| id | UUID |
| name | VARCHAR(100), UNIQUE |
| category | VARCHAR(100) |
| icon | TEXT |
| official_url | TEXT |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

Índices

- name (UNIQUE)

---

## services

Descripción

Servicios profesionales ofrecidos, agrupados por línea de negocio.

| Columna | Tipo | Restricciones |
|----------|------|---------------|
| id | UUID | PK |
| service_line_id | UUID | FK → service_lines.id, NULL — NUEVO (CH-TECH V2) |
| title | VARCHAR(255) | NOT NULL |
| slug | VARCHAR(150) | UNIQUE |
| description | TEXT | NULL |
| featured | BOOLEAN | DEFAULT FALSE |
| active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

Índices

- service_line_id — NUEVO (CH-TECH V2)

---

## articles

Descripción

Publicaciones técnicas.

| Columna | Tipo |
|----------|------|
| id | UUID |
| author_id | UUID |
| slug | VARCHAR(150) |
| title | VARCHAR(255) |
| summary | TEXT |
| content | TEXT |
| cover_image | TEXT |
| reading_time | INTEGER |
| published | BOOLEAN |
| published_at | TIMESTAMP |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

Índices

- slug
- published

---

## case_studies

Descripción

Análisis técnico de un proyecto.

| Columna | Tipo |
|----------|------|
| id | UUID |
| project_id | UUID |
| challenge | TEXT |
| solution | TEXT |
| architecture | TEXT |
| lessons_learned | TEXT |
| metrics | JSON — **Postgres → MySQL:** era `JSONB`, ver nota en `companies.social_links`. |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

---

## clients — NUEVO (CH-TECH V2)

Descripción

Empresas cliente de CH-TECH.

| Columna | Tipo | Restricciones |
|----------|------|---------------|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| logo | TEXT | NULL |
| industry | VARCHAR(150) | NULL |
| website_url | TEXT | NULL |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

---

## testimonials — NUEVO (CH-TECH V2)

Descripción

Citas de clientes sobre el trabajo de CH-TECH.

| Columna | Tipo | Restricciones |
|----------|------|---------------|
| id | UUID | PK |
| author_name | VARCHAR(150) | NOT NULL |
| author_role | VARCHAR(150) | NULL |
| client_id | UUID | FK → clients.id, NULL |
| project_id | UUID | FK → projects.id, NULL |
| content | TEXT | NOT NULL |
| rating | SMALLINT | NULL, CHECK (rating IS NULL OR rating BETWEEN 1 AND 5) |
| featured | BOOLEAN | DEFAULT FALSE |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

Índices

- client_id
- project_id
- featured

---

## products — NUEVO (CH-TECH V2)

Descripción

Catálogo de productos SaaS propios de CH-TECH (ver ADR-0013 — no almacena estado operativo del producto, solo catálogo).

| Columna | Tipo | Restricciones |
|----------|------|---------------|
| id | UUID | PK |
| slug | VARCHAR(150) | UNIQUE, NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| short_description | TEXT | NULL |
| full_description | TEXT | NULL |
| status | VARCHAR(50) | NOT NULL, CHECK (status IN ('WAITLIST','BETA','LIVE')) |
| url | TEXT | NULL |
| logo | TEXT | NULL |
| featured | BOOLEAN | DEFAULT FALSE |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

Índices

- slug
- status

---

## partners — NUEVO (CH-TECH V2)

Descripción

Alianzas tecnológicas o de negocio de CH-TECH.

| Columna | Tipo | Restricciones |
|----------|------|---------------|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| logo | TEXT | NULL |
| partnership_type | VARCHAR(100) | NULL |
| website_url | TEXT | NULL |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

---

## refresh_tokens

Descripción

Representa una sesión autenticada. Permite renovar el access token y revocar una sesión (logout).

El valor del token nunca se almacena en texto plano, solo su hash.

| Columna | Tipo | Restricciones |
|----------|------|---------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL |
| token_hash | VARCHAR(255) | NOT NULL, UNIQUE |
| issued_at | TIMESTAMP | NOT NULL |
| expires_at | TIMESTAMP | NOT NULL |
| revoked_at | TIMESTAMP | NULL |
| user_agent | TEXT | NULL |
| ip_address | VARCHAR(45) | NULL |

No incluye `updated_at`: un refresh token es inmutable una vez emitido; `revoked_at` es su único cambio de estado posible.

Índices

- user_id
- token_hash
- expires_at

Retención

- Ninguna fila se borra en el flujo normal de la aplicación (login/refresh/logout solo insertan o revocan). `app/db/purge_refresh_tokens.py` borra las filas expiradas o revocadas hace más de `REFRESH_TOKEN_RETENTION_DAYS` (30 por defecto) — debe ejecutarse periódicamente vía cron en el host (ver DEPLOYMENT.md), nunca desde una ruta HTTP.

---

## contact_requests

Descripción

Solicitudes recibidas mediante el formulario. Extendida en CH-TECH V2 con contexto comercial opcional — no rompe el contrato existente de `POST /contact`.

| Columna | Tipo | Restricciones |
|----------|------|---------------|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| email | VARCHAR(255) | NOT NULL |
| company | VARCHAR(255) | NULL |
| subject | VARCHAR(255) | NULL |
| message | TEXT | NOT NULL |
| interested_service_line_id | UUID | FK → service_lines.id, NULL — NUEVO (CH-TECH V2) |
| source | VARCHAR(100) | NULL — NUEVO (CH-TECH V2) |
| status | VARCHAR(50) | NOT NULL |
| created_at | TIMESTAMP | NOT NULL |

Índices

- status
- email
- created_at
- interested_service_line_id — NUEVO (CH-TECH V2)

---

# Tablas de Relación

## project_technologies

Relaciona proyectos con tecnologías.

| Columna | Tipo |
|----------|------|
| project_id | UUID |
| technology_id | UUID |

PK

(project_id, technology_id)

---

## article_technologies

Relaciona artículos con tecnologías.

| Columna | Tipo |
|----------|------|
| article_id | UUID |
| technology_id | UUID |

PK

(article_id, technology_id)

---

# Relaciones

User 1───N Article

User 1───N RefreshToken

User 1───0..1 TeamMember (CH-TECH V2)

Project 1───N CaseStudy

Project N───N Technology

Project N───0..1 Client (CH-TECH V2)

Article N───N Technology

ServiceLine 1───N Service (CH-TECH V2)

ServiceLine 1───N ContactRequest, opcional (CH-TECH V2)

Client 1───N Project, opcional (CH-TECH V2)

Client 1───N Testimonial, opcional (CH-TECH V2)

Project 1───N Testimonial, opcional (CH-TECH V2)

---

# Restricciones

- email debe ser único (comparación case-insensitive; normalizado a minúsculas antes de guardar).
- slug debe ser único dentro de cada entidad.
- No pueden existir proyectos sin título.
- No pueden existir artículos publicados sin published_at.
- service_line_id en services es nullable por ahora (CH-TECH V2): forzar NOT NULL antes de que exista una UI de asignación (Fase 6) implicaría inventar un valor de relleno sin base real. Se vuelve obligatorio en una migración posterior, una vez que haya forma real de asignarlo.
- La tabla companies nunca tiene más de un registro (CH-TECH V2).
- Los registros de auditoría son obligatorios.

---

# Estrategia de Migraciones

Todas las modificaciones al esquema deberán realizarse mediante Alembic, aplicadas con la credencial `chtech_migrator` — la aplicación en ejecución usa `chtech_app`, que deliberadamente no tiene privilegios DDL (`CREATE`/`ALTER`/`DROP`). Ver ADR-0014 y `scripts/migration_to_sql.py` para generar el DDL como texto revisable antes de aplicarlo.

Nunca se modificará manualmente una base de datos de producción.

Cada migración deberá ser:

- Reversible.
- Atómica.
- Versionada.
- Revisada mediante Pull Request.

---

# Evolución del Esquema

Cualquier cambio estructural importante deberá estar respaldado por:

- Un ADR (si afecta la arquitectura).
- Una migración Alembic.
- Actualización de este documento.
