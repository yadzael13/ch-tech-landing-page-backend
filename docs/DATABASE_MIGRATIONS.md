# Database Migrations

## Objetivo

Este documento define los estándares y el flujo de trabajo para la evolución del esquema de base de datos de CH-TECH.

Todas las modificaciones estructurales deberán realizarse mediante migraciones versionadas utilizando Alembic.

No se permite modificar manualmente el esquema de una base de datos en ningún entorno.

---

# Herramientas

## Base de Datos

- MySQL 8.4 (migrado desde PostgreSQL — ver ADR-0014)

## ORM

- SQLAlchemy 2.x

## Migraciones

- Alembic

---

# Principios

Las migraciones deben ser:

- Versionadas
- Reproducibles
- Reversibles
- Atómicas
- Revisadas mediante Pull Request

Cada migración representa un único cambio de negocio.

Ejemplos:

✅ Crear tabla `projects`

✅ Agregar columna `featured`

✅ Crear índice sobre `slug`

❌ Crear cinco tablas y modificar tres existentes en una sola migración.

---

# Flujo de Trabajo

Todo cambio en la base de datos seguirá el siguiente proceso:

1. Actualizar `DATA_MODEL.md` si cambia el dominio.
2. Actualizar `DATABASE_SCHEMA.md`.
3. Generar la migración con Alembic.
4. Revisar el SQL generado (`python scripts/migration_to_sql.py` — escribe el DDL en `migration-review/` para revisión, sin aplicarlo).
5. Ejecutar la migración en desarrollo.
6. Ejecutar pruebas.
7. Enviar Pull Request.
8. Ejecutar la migración en producción mediante el pipeline.

---

# Convención de Nombres

Las migraciones deberán utilizar nombres descriptivos.

Ejemplos:

create_projects_table

add_featured_to_projects

create_project_technology_relation

add_indexes_to_articles

rename_contact_status

Evitar nombres genéricos como:

revision_001

migration_fix

update_table

---

# Reglas

## Nunca modificar una migración ya aplicada.

Una vez que una migración forma parte del historial del proyecto, no deberá editarse.

Los cambios posteriores deberán realizarse mediante una nueva migración.

---

## Nunca modificar la base de datos manualmente.

Todos los cambios deben quedar registrados en Alembic.

Esto garantiza:

- Historial reproducible.
- Auditoría.
- Consistencia entre entornos.

Reforzado a nivel de motor (no solo de convención) desde ADR-0014: Alembic
corre con la credencial `chtech_migrator` (única con privilegios DDL); la
aplicación en ejecución usa `chtech_app`, que MySQL rechaza si intenta
`CREATE`/`ALTER`/`DROP`. Esto también cubre a cualquier asistente de IA que
opere sobre el backend en ejecución — no puede alterar tablas aunque lo
intente, porque la credencial que usa la app no tiene ese privilegio.

---

## Una responsabilidad por migración.

Cada migración debe resolver un único objetivo.

Incorrecto:

- Crear usuarios.
- Crear proyectos.
- Crear artículos.

Correcto:

Migración 1

Crear tabla users.

Migración 2

Crear tabla projects.

Migración 3

Crear tabla articles.

> **Excepción histórica:** la migración `0001_baseline_mysql_schema.py` de
> este repositorio crea las 15 tablas + 2 tablas de asociación en una sola
> migración. Es un caso deliberado y único: reemplaza las 21 migraciones
> incrementales del monorepo original (varias de las cuales existían solo
> para particularidades de Postgres) al migrar a MySQL sin datos de
> producción que replayar (ver ADR-0014). No es el patrón a seguir para
> cambios futuros — esos sí deben respetar una responsabilidad por
> migración.

---

# Revisión de Migraciones

Antes de aceptar una migración se verificará:

- El nombre describe correctamente el cambio.
- El SQL generado es el esperado.
- Existe rollback (`downgrade()`).
- No elimina información accidentalmente.
- No rompe compatibilidad con la aplicación.

---

# Rollback

Toda migración debe implementar:

- upgrade()
- downgrade()

No se aceptan migraciones irreversibles salvo que exista una justificación documentada mediante un ADR.

---

# Datos Iniciales (Seed Data)

Las migraciones no deben insertar datos de negocio.

Únicamente podrán crear:

- Roles iniciales.
- Configuración mínima del sistema.
- Catálogos necesarios para el funcionamiento.

Los datos de ejemplo deberán cargarse mediante procesos de seed independientes.

---

# Entornos

## Desarrollo

Las migraciones se ejecutarán automáticamente al iniciar el entorno Docker si existen cambios pendientes.

## Testing

Cada suite de pruebas utilizará una base de datos limpia y aplicará las migraciones antes de ejecutarse.

## Producción

Las migraciones se ejecutarán únicamente desde el pipeline de CI/CD.

No se ejecutarán manualmente sobre el servidor.

---

# Compatibilidad

Siempre que sea posible, los cambios deberán ser compatibles hacia atrás.

Cuando una modificación rompa compatibilidad:

1. Crear un ADR.
2. Documentar el impacto.
3. Definir un plan de migración.
4. Comunicar el cambio antes del despliegue.

---

# Definition of Done

Una migración se considera finalizada cuando:

- Existe una migración Alembic.
- `upgrade()` funciona correctamente.
- `downgrade()` funciona correctamente.
- La documentación está actualizada.
- Las pruebas pasan correctamente.
- La revisión de código ha sido aprobada.

---

# Buenas Prácticas

## Sí

- Crear migraciones pequeñas.
- Revisar el SQL generado.
- Mantener compatibilidad cuando sea posible.
- Versionar todos los cambios.
- Documentar cambios importantes.

## No

- Editar migraciones antiguas.
- Ejecutar SQL manual en producción.
- Combinar múltiples cambios de negocio en una sola migración.
- Omitir el rollback sin justificación.
- Saltarse la revisión de código.

---

# Relación con otros documentos

Este documento complementa:

- `DATA_MODEL.md` → Modelo de dominio.
- `DATABASE_SCHEMA.md` → Diseño físico.
- `ENGINEERING.md` → Estándares de desarrollo.
- `CI_CD.md` → Automatización de despliegues.
- `PROJECT_RULES.md` → Reglas generales del proyecto.