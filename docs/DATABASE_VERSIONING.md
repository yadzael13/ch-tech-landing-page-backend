# Database Versioning

## Objetivo

Este documento define la estrategia de versionado del esquema de base de datos de CH-TECH.

Su propósito es garantizar que todos los entornos (desarrollo, pruebas, staging y producción) compartan el mismo historial de migraciones y que la evolución del esquema sea controlada, reproducible y auditable.

---

# Principios

El esquema de la base de datos es código.

Toda modificación deberá ser:

- Versionada.
- Reproducible.
- Revisable.
- Auditable.
- Compatible con el flujo de desarrollo.

Nunca existirá una modificación manual del esquema fuera del sistema de migraciones.

---

# Fuente de Verdad

La única fuente de verdad del estado del esquema será el historial de migraciones de Alembic.

No se considerará válida ninguna modificación realizada directamente sobre la base de datos.

---

# Estrategia de Versionado

Cada migración representa una nueva versión del esquema.

Ejemplo:

v1

↓

create_users_table

↓

v2

↓

create_projects_table

↓

v3

↓

add_featured_to_projects

↓

v4

↓

create_articles_table

Cada versión depende de la anterior.

No se permiten versiones aisladas.

---

# Identificación

Cada versión será identificada por:

- Revision ID (Alembic)
- Nombre descriptivo
- Fecha
- Autor
- Pull Request asociado

Ejemplo

Revision

7af8c11d1b3e

Nombre

create_projects_table

Fecha

2026-08-10

---

# Estados del Esquema

Todos los entornos deberán encontrarse en alguno de los siguientes estados:

Current

El esquema coincide con la última migración.

Outdated

Existen migraciones pendientes.

Migrating

Se está aplicando una nueva versión.

Failed

La migración falló y requiere intervención.

Unknown

El estado no puede determinarse.

---

# Compatibilidad

Las migraciones deberán mantener compatibilidad hacia atrás siempre que sea posible.

Cuando un cambio rompa compatibilidad se deberá:

1. Crear un ADR.
2. Documentar el impacto.
3. Definir un plan de transición.
4. Actualizar la documentación.

---

# Entornos

## Desarrollo

Siempre deberá utilizar la última versión del esquema.

Las migraciones pendientes deberán ejecutarse automáticamente al iniciar el entorno.

---

## Testing

Cada ejecución comenzará desde una base limpia.

Las migraciones deberán ejecutarse completamente antes de iniciar las pruebas.

---

## Staging

Debe ejecutar exactamente la misma versión que producción antes de recibir nuevas migraciones.

---

## Producción

Solo podrá actualizarse mediante el pipeline de CI/CD.

No se permiten migraciones manuales.

---

# Flujo de Versionado

Nueva funcionalidad

↓

Actualizar DATA_MODEL.md

↓

Actualizar DATABASE_SCHEMA.md

↓

Crear migración Alembic

↓

Ejecutar pruebas

↓

Pull Request

↓

Merge

↓

Pipeline CI/CD

↓

Aplicar migración

↓

Nueva versión del esquema

---

# Resolución de Conflictos

Cuando dos ramas generen migraciones simultáneamente:

1. Actualizar la rama con main.
2. Resolver el conflicto mediante una migración de merge de Alembic.
3. Verificar que exista un único head.
4. Ejecutar nuevamente todas las migraciones.

Nunca modificar una migración ya publicada para resolver conflictos.

---

# Reglas

## Permitido

- Crear nuevas migraciones.
- Agregar columnas.
- Crear índices.
- Crear restricciones.
- Agregar tablas.

---

## Requiere aprobación

- Eliminar columnas.
- Eliminar tablas.
- Cambiar tipos de datos.
- Renombrar tablas.
- Renombrar columnas.

Estos cambios deberán estar respaldados por un ADR.

---

# Rollback

Toda versión deberá poder revertirse.

El método downgrade() deberá mantenerse funcional.

No se aceptarán migraciones irreversibles salvo aprobación explícita.

---

# Integridad

Antes de liberar una nueva versión deberán verificarse:

- Todas las migraciones ejecutan correctamente.
- No existen múltiples heads.
- El historial es lineal o tiene merges documentados.
- El esquema coincide con DATABASE_SCHEMA.md.
- Las pruebas pasan correctamente.

---

# CI/CD

El pipeline deberá validar automáticamente:

- Alembic sin conflictos.
- Un único head.
- Migraciones reversibles.
- Sin diferencias entre modelos y migraciones.
- Base creada desde cero correctamente.
- Upgrade completo.
- Downgrade completo.
- Upgrade nuevamente.

---

# Métricas

Se recomienda monitorear:

- Número de migraciones.
- Tiempo promedio de ejecución.
- Tiempo de rollback.
- Versiones desplegadas por entorno.
- Fallos de migración.

---

# Definición de Hecho

Una nueva versión del esquema estará completa cuando:

- Existe una migración Alembic.
- El esquema está documentado.
- DATA_MODEL.md está actualizado.
- DATABASE_SCHEMA.md está actualizado.
- Las pruebas pasan.
- El pipeline CI/CD es exitoso.
- El despliegue se realizó correctamente.

---

# Relación con otros documentos

Este documento complementa:

- DATA_MODEL.md
- DATABASE_SCHEMA.md
- DATABASE_MIGRATIONS.md
- ENGINEERING.md
- CI_CD.md
- PROJECT_RULES.md