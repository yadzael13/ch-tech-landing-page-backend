# ADR-0012

## Título

Formalizar Clean Architecture (domain / application / infrastructure / api) en el backend, antes de escalar el dominio con CH-TECH V2.

## Estado

Aceptado

## Fecha

2026-08-03

---

## Contexto

CH-TECH pivota de portafolio personal a plataforma oficial de una startup de Ingeniería de Software e IA (ver VISION.md). Ese pivote agrega entidades de dominio nuevas: `Company`, `TeamMember`, `ServiceLine`, `Client`, `Testimonial`, `Product`, `Partner`, además de extender `ContactRequest` (ver DATA_MODEL.md).

El backend actual es una estructura pragmática por capas: `api/` (routers FastAPI), `core/` (config, seguridad, email, rate limiting), `db/` (sesión, seed), `models/` (SQLAlchemy) y `schemas/` (Pydantic). No existen `domain/` ni `application/` como capas explícitas — los modelos SQLAlchemy funcionan a la vez como entidad de dominio y como registro de persistencia, y la lógica de casos de uso vive implícita dentro de los routers.

ENGINEERING.md y VISION.md declaran "Clean Architecture" como estándar del proyecto desde su origen (ver PHASE 0/1 en ROADMAP.md), pero el código nunca implementó la separación completa. Multiplicar entidades sobre la estructura pragmática actual hace más caro resolver esta discrepancia después: cada entidad nueva repetiría el mismo patrón sin capa de dominio ni de aplicación.

---

## Decisión

Se formaliza la separación en cuatro capas descrita en ARCHITECTURE.md — `domain/`, `application/`, `infrastructure/`, `api/` — con una única regla de dependencia: las capas externas dependen de las internas, nunca al revés.

Las entidades nuevas de CH-TECH V2 se construyen directamente sobre esta arquitectura objetivo. Las entidades existentes (`Project`, `Technology`, `Service`, `Article`, `CaseStudy`, `User`, `RefreshToken`, `ContactRequest`) migran de forma incremental, módulo por módulo, como trabajo explícito de la Fase 7 del ROADMAP — antes de agregar las entidades nuevas, no en paralelo ni después.

Esta ADR es una decisión de documentación y de plan (Etapa 2/3 de la migración a CH-TECH V2); la ejecución del refactor ocurre como fases de implementación separadas, cada una con su propio PR, siguiendo PROJECT_RULES.md ("nunca modificar más de una responsabilidad por PR").

---

## Alternativas

- **Mantener la estructura pragmática actual y corregir la documentación para que deje de prometer Clean Architecture.** Menor costo inmediato, evita abstracción prematura mientras el dominio es pequeño. Se descarta porque el dominio está a punto de crecer de forma significativa (5 entidades nuevas) y el costo de introducir las capas después, con más entidades ya acopladas a routers, es mayor que introducirlas ahora.
- **Reescribir todo el backend de una sola vez.** Se descarta explícitamente: el brief de CH-TECH V2 pide evolucionar, no reescribir, preservando la calidad ya alcanzada.

---

## Consecuencias

### Positivas

- El código deja de contradecir lo que ya declaran ENGINEERING.md y VISION.md.
- Las entidades nuevas de V2 no heredan el acoplamiento actual entre modelo SQLAlchemy y lógica de negocio.
- Los casos de uso quedan testeables sin levantar FastAPI ni una base de datos real (se puede mockear el puerto de repositorio).

### Negativas

- Más archivos e indirección por entidad que el patrón plano actual.
- La migración incremental de las 7 entidades existentes es trabajo real, no solo documental — se planifica en el plan de migración (ver plan de migración, Fase 7).

---

## Referencias

https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html

ARCHITECTURE.md, ENGINEERING.md, ROADMAP.md (Fase 7)
