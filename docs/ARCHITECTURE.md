# Architecture

## Objetivo

Este documento define la arquitectura lógica del backend de CH-TECH: las capas del sistema, sus límites y la regla de dependencia entre ellas.

Para la topología de despliegue (qué corre en qué entorno, en qué servicio de infraestructura) ver DEPLOYMENT.md. Este documento no la repite.

---

# Estilo arquitectónico

CH-TECH adopta **Clean Architecture** (Ports & Adapters) para el backend, formalizada en ADR-0012.

La regla de dependencia es única: **las capas externas dependen de las internas, nunca al revés.** El dominio no importa nada de FastAPI, SQLAlchemy ni Pydantic.

```
            ┌─────────────────────────────┐
            │      api (FastAPI)          │  routers, schemas Pydantic, deps
            ├─────────────────────────────┤
            │   infrastructure            │  modelos SQLAlchemy, repositorios,
            │                             │  seguridad, email, rate limiting
            ├─────────────────────────────┤
            │   application               │  casos de uso, puertos (interfaces
            │                             │  de repositorio)
            ├─────────────────────────────┤
            │   domain                    │  entidades, value objects, reglas
            │                             │  de negocio — sin dependencias
            │                             │  externas
            └─────────────────────────────┘
```

---

## domain/

Entidades y value objects del negocio, tal como se describen en DATA_MODEL.md. Python puro, sin imports de FastAPI, SQLAlchemy ni Pydantic. Aquí viven las reglas de negocio (p. ej. "un refresh token se usa una única vez").

## application/

Casos de uso (un caso de uso = una operación de negocio, p. ej. `CreateProject`, `PublishArticle`, `RegisterContactRequest`). Cada caso de uso depende de **puertos** (interfaces de repositorio) definidos en esta misma capa, nunca de una implementación concreta.

## infrastructure/

Implementación concreta de los puertos: modelos SQLAlchemy, repositorios que los usan, integración con Resend (email), Redis (rate limiting) y JWT (seguridad). Esta capa depende de `application` y `domain`, nunca al revés.

## api/

Routers de FastAPI, schemas Pydantic de request/response, y el wiring de dependencias (`Depends`) que conecta cada endpoint con su caso de uso. Es la capa más externa: lo único que sabe que existe HTTP.

---

# Estado actual

El código hoy es una estructura pragmática por capas (`api / core / db / models / schemas`) sin `domain/` ni `application/` explícitos — los casos de uso viven implícitos dentro de los routers y los modelos SQLAlchemy hacen doble función de entidad de dominio y de persistencia.

ADR-0012 decide formalizar la separación completa descrita arriba. La migración de la estructura actual hacia esta arquitectura es incremental (ver ROADMAP.md, Fase 7) y precede a la incorporación de las entidades nuevas de CH-TECH V2: el dominio nuevo se construye directamente sobre la arquitectura objetivo, no sobre la estructura pragmática actual.

---

# Principios

- Separation of Concerns: cada capa tiene una única razón para cambiar.
- SOLID, DRY, KISS aplican dentro de cada capa (ver ENGINEERING.md).
- Los modelos SQLAlchemy no se exponen directamente en las respuestas de la API — la serialización pasa siempre por un schema Pydantic.
- Los value objects (Email, Slug, Url, Image, Password, MarkdownContent — ver DATA_MODEL.md) encapsulan su propia validación; no se valida el mismo formato en dos capas distintas.
