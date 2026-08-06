# CI/CD

> Este documento cubre el backend (`.github/workflows/ci.yml` de este repo). El pipeline del frontend vive en `ch-tech-landing-page-frontend/docs/CI_CD.md`.

## Objetivo

Garantizar que ningún cambio llegue a main sin cumplir los estándares de calidad.

---

## Pipeline

Cada Pull Request ejecutará automáticamente:

- Lint Backend (Ruff, Black)
- Type Checking (MyPy)
- Tests (pytest)
- Coverage
- Database Validation (ver abajo)
- Build Docker
- Security Scan (Bandit, Trivy, pip-audit)

---

## Merge Policy

No se permite hacer merge si falla alguno de los siguientes:

- lint

- tests

- cobertura mínima

- type checking

- build

- análisis estático

---

## Cobertura mínima

90% (`pytest --cov`, `pyproject.toml`)

---

## Ramas protegidas

main

develop

No se permite hacer push directo.

---

## Database Validation

El pipeline ejecutará automáticamente:

- Alembic upgrade
- Alembic downgrade
- Verificación de un único head
- Creación de la base desde cero
- Compatibilidad de migraciones
