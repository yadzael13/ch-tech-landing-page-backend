# Audience

AI Assistant

Antes de modificar cualquier archivo:

1 Leer la documentación relevante.

2 No asumir requisitos.

3 Preguntar si existen dudas.

4 No instalar dependencias sin justificar.

5 Mantener componentes pequeños.

6 Explicar cada decisión técnica.

7 No modificar archivos fuera del alcance de la tarea.

8 Actualizar documentación si cambia la arquitectura.

9 Escribir código siguiendo los estándares definidos.

10 En el backend seguir TDD de forma obligatoria.

11 Nunca hacer commit directamente sobre `develop` ni `main`. Antes de empezar cualquier cambio, crear una rama dedicada a ese cambio (branch por Sprint/iniciativa, con commits usando Conventional Commits) y trabajar ahí.

12 Si la rama posicionada en local es `develop`, hacer `git pull` de los últimos cambios antes de crear la rama nueva.

13 Nunca ejecutar `git push` — ni sobre `develop`/`main` ni sobre la rama de trabajo. Subir la rama a origin es una decisión del desarrollador, no del agente.

14 Nunca modificar la estructura de las tablas (crear, alterar o eliminar tablas/columnas/índices) fuera de una migración de Alembic nueva y revisada por PR. La aplicación en ejecución se conecta con `chtech_app`, una credencial de MySQL sin privilegios DDL — MySQL rechaza cualquier `CREATE`/`ALTER`/`DROP` intentado por esa vía, aunque provenga de este mismo asistente (ver ADR-0014, `docs/adr/0014-mysql-database-privilege-separation.md`). Si una tarea requiere cambiar el esquema, generar una migración con Alembic y aplicarla con la credencial `chtech_migrator` — nunca ejecutar SQL manual contra la base de datos.