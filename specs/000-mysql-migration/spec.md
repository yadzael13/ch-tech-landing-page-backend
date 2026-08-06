# Spec 000: Migración a MySQL y separación de repos

## Qué

Separar el backend del monorepo original `ch-tech` en su propio repositorio
(`ch-tech-landing-page-backend`), migrando su base de datos de PostgreSQL a
MySQL, preservando exactamente el mismo comportamiento observable (API,
contrato de datos, flujos de auth, admin CRUD) y agregando una garantía
nueva: ni la aplicación en ejecución ni ningún asistente de IA pueden
alterar la estructura de las tablas.

## Por qué

- El proyecto pasa de vivir en un monorepo (`frontend/` + `backend/`) a un
  ecosistema de repos independientes (`ch-tech-ecosystem`), reflejando que
  ambas apps ya se desplegaban de forma independiente (Vercel vs. EC2).
- MySQL reemplaza a PostgreSQL como motor de base de datos (decisión de
  negocio, fuera del alcance de esta spec justificarla).
- Se requiere que ningún asistente de IA — ni el que edita este repo, ni una
  futura feature de IA en producto — pueda modificar el esquema de la base
  de datos. Antes de esta migración no existía ninguna garantía técnica
  para eso, solo convención documentada.

## Requisitos

1. El backend debe seguir sirviendo exactamente el mismo contrato de API
   (`docs/API.md`) — sin cambios de forma en request/response.
2. Las 15 tablas + 2 tablas de asociación del esquema original deben existir
   en MySQL con tipos/constraints equivalentes (ver `docs/DATABASE_SCHEMA.md`).
3. La aplicación en ejecución debe conectarse con una credencial MySQL sin
   privilegios DDL (`chtech_app`); los cambios de esquema deben requerir una
   credencial separada (`chtech_migrator`), usada únicamente por Alembic.
4. Debe existir un script que genere el DDL completo como SQL revisable
   (`scripts/migration_to_sql.py`).
5. Alcance de datos: solo estructura — la base nueva nace vacía y se
   repuebla con el seed existente. No hay migración de filas reales desde
   Postgres (decisión ya tomada, ver plan de migración).
6. El repositorio original (`ch-tech`) no se modifica ni se borra.

## Criterios de aceptación

- [x] `alembic upgrade head` crea el esquema completo desde cero contra MySQL 8.4.
- [x] `alembic downgrade base` → `alembic upgrade head` es reversible sin errores.
- [x] `alembic check` reporta cero drift entre los modelos y la migración.
- [x] Un test conectado como `chtech_app` que intenta `ALTER TABLE` recibe el error MySQL 1142 (command denied).
- [x] El mismo test confirma que `chtech_app` sigue pudiendo leer/escribir datos normalmente.
- [x] El seed (`python -m app.db.seed`) puebla admin, tecnologías, company y team member sin errores.
- [x] `scripts/migration_to_sql.py` genera un archivo `.sql` revisable con el DDL completo.
- [x] Suite completa de pytest (`--cov`) en verde contra MySQL real: 564 passed, 98.47% de cobertura (mínimo requerido: 90%).
