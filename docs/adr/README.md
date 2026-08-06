# Architecture Decision Records

Este directorio documenta las decisiones arquitectónicas relevantes del
backend de CH-TECH. Numeración heredada del repo monorepo original
(`ch-tech`) — no se renumeró al separar el repo, para no romper las
referencias cruzadas entre ADRs (ej. "Reemplazada por ADR-0011"). Las ADRs
sobre el frontend (Next.js, Vercel) quedaron en
`ch-tech-landing-page-frontend`; ver ese repo para ADR-0001 y ADR-0006.

| ADR | Estado | Descripción |
|-----|--------|-------------|
| ADR-0002 | Aceptado | Adoptar licencia MIT |
| ADR-0003 | Aceptado | Authentication Scope |
| ADR-0004 | Aceptado | Versionado de API |
| ADR-0005 | Aceptado | SQLAlchemy 2.x, Alembic y Pydantic v2 (actualizada: motor MySQL, ver ADR-0014) |
| ADR-0007 | Aceptado | Redis para rate limiting |
| ADR-0008 | Aceptado | Stack de observabilidad |
| ADR-0009 | Reemplazada por ADR-0010 | Cloudflare delante del backend |
| ADR-0010 | Reemplazada por ADR-0011 | AWS App Runner para el backend |
| ADR-0011 | Aceptado | Backend en EC2 autogestionado |
| ADR-0012 | Aceptado | Clean Architecture: domain / application / infrastructure / api |
| ADR-0013 | Aceptado | `Product` es catálogo, no infraestructura de producto SaaS |
| ADR-0014 | Aceptado | Migración a MySQL y separación de privilegios (`chtech_app` / `chtech_migrator`) |