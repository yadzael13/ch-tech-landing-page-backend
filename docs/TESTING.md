# Testing Strategy

> Este documento cubre el backend. La estrategia de testing del frontend vive en `ch-tech-landing-page-frontend/docs/TESTING.md`.

Backend

Desarrollo mediante TDD.

Flujo obligatorio

1 Escribir prueba

2 Ejecutar prueba

3 Ver falla

4 Implementar

5 Ejecutar pruebas

6 Refactorizar

Nunca escribir código antes del test.

Cobertura mínima: 90% (`pytest --cov`, `pyproject.toml`).

Incluye una verificación explícita del límite de privilegios de base de datos (`tests/test_db_privilege_boundary.py`) — ver ADR-0014.