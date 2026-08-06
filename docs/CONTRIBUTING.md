# Audience

Contributors

# Reglas

Siempre leer la documentación antes de escribir código.

No modificar archivos fuera del alcance de la tarea.

Una tarea por Pull Request.

Componentes pequeños, una única responsabilidad.

Python con type hints estrictos (MyPy `strict = true`).

TDD obligatorio (ver `docs/TESTING.md`) — nunca escribir código de producción antes que su test.

No instalar dependencias sin justificarlo.

Actualizar documentación cuando cambie la arquitectura.

Todo debe funcionar mediante Docker (`docker compose up --build`).

# Desarrollo guiado por especificaciones

Para cambios no triviales: crear `specs/NNN-nombre-feature/` con `spec.md` (qué/por qué), `plan.md` (cómo) y `tasks.md` (checklist ordenado, TDD-first). Ver `specs/000-mysql-migration/` como ejemplo real. Complementa, no reemplaza, el patrón de ADRs (`docs/adr/`) para decisiones cross-cutting.