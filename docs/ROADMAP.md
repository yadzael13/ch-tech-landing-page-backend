# CH-TECH Roadmap

## Objetivo

Construir la plataforma oficial de CH-TECH, startup de Ingeniería de Software e IA, que sirva como:

- Sitio corporativo con las cinco líneas de negocio
- Showcase técnico y de casos de estudio
- Generador de leads comerciales
- Catálogo de futuros productos SaaS propios

Las fases 0–6 se completaron bajo el enfoque anterior de portafolio personal (ver VISION.md para el histórico) y no se modifican — son historial verificable en el propio repositorio. A partir de la Fase 7, el roadmap sigue el reposicionamiento a CH-TECH V2.

---

# Estado del Proyecto

🟢 Completado

🟡 En progreso

⚪ Pendiente

🔴 Bloqueado

---

# PHASE 0 - Ingeniería del Proyecto

Objetivo

Preparar una base sólida antes de escribir código.

### TASK-001

🟢 Crear repositorio Git

### TASK-002

🟢 Crear documentación inicial

- VISION.md
- TECH_STACK.md
- ARCHITECTURE.md
- ROADMAP.md

### TASK-003

🟢 Configurar Docker

### TASK-004

🟢 Configurar proyecto Next.js

### TASK-005

🟢 Configurar FastAPI

### TASK-006

🟢 Configurar Docker Compose

### TASK-007

🟢 Configurar GitHub Actions

- CI (lint, tests, coverage, build)
- Security scanning
- Dependabot

### TASK-008

🟢 Configurar Husky

### TASK-009

🟢 Configurar Prettier

### TASK-010

🟢 Configurar ESLint

---

# PHASE 1 - Calidad

Objetivo

Garantizar calidad desde el primer commit.

### TASK-011

🟢 Configurar Ruff

### TASK-012

🟢 Configurar Black

### TASK-013

🟢 Configurar MyPy

### TASK-014

🟢 Configurar pytest

### TASK-015

🟢 Configurar cobertura

- Gate mínimo: 90%

### TASK-016

🟢 Configurar Bandit

### TASK-017

🟢 Configurar Dependabot

---

# PHASE 2 - Landing

### TASK-018

🟢 Navbar

### TASK-019

🟢 Hero

### TASK-020

🟢 Sobre mí

### TASK-021

🟢 Tecnologías

### TASK-022

🟢 Servicios

### TASK-023

🟢 Proyectos

### TASK-024

🟢 Footer

### TASK-024a

🟢 Contacto (formulario funcional, `POST /contact`)

- No numerada originalmente; agregada por ser requisito de VISION.md
  ("formulario de contacto funcionando") y porque el backend ya la soportaba.

---

# PHASE 3 - Backend

### TASK-025

🟢 Diseñar modelos SQLAlchemy

### TASK-026

🟢 Primera migración Alembic

### TASK-027

🟢 Seed inicial


### TASK-028

🟢 API Base

### TASK-029

🟢 Health Check

### TASK-030

🟢 Autenticación

- JWT (access + refresh con rotación)
- Login / Refresh / Logout

### TASK-031

🟢 Logging

### TASK-032

🟢 Rate Limiting

### TASK-032a

🟢 CRUD API de recursos de contenido (pública + admin)

- Projects
- Technologies
- Services
- Articles
- Case Studies
- Contact (con notificación async vía Resend)

---

# PHASE 4 - CI/CD

### TASK-033

🟢 Docker Production

- `docker/backend/Dockerfile.prod` (multi-stage, no-root, sin migraciones en
  el `CMD`) — build local y `curl /health` verificados. Destino de
  despliegue: EC2 autogestionado vía Docker Compose (ver ADR-0011).

### TASK-034

⚪ Deploy

### TASK-035

⚪ Monitoring

### TASK-036

⚪ Observability

---

# PHASE 5 - Optimización

Objetivo

SEO, Performance, Accesibilidad y Core Web Vitals del sitio público. Desglosado en tasks concretas a partir de una auditoría real (Lighthouse contra build de producción + revisión de código), no de una lista genérica.

### TASK-053

🟢 Corregir el congelamiento de contenido por generación estática

- Hallazgo de la auditoría: `/` se prerenderizaba como contenido 100% estático en build (`next build` la marcaba `○`), porque los fetchers de `lib/api/content.ts` usan `fetch()` sin config de cache — Next.js los cacheaba indefinidamente. Un cambio en el panel admin (Company, Team, Testimonials, Clients, Products, ServiceLines) no se reflejaba en el sitio público sin un redeploy. Corregido con `next: { revalidate: 60 }` en `apiFetch` (`lib/api/client.ts`) — no-op en peticiones no GET y en fetches del navegador (admin, "use client"). Verificado en el build: `/` pasa a `Revalidate: 1m / Expire: 1y`.

### TASK-054

🟢 `robots.ts`, `sitemap.ts` y `NEXT_PUBLIC_SITE_URL`

- Hallazgo: no existía ni robots.txt ni sitemap.xml. `metadataBase` tampoco estaba configurado (URLs relativas en OpenGraph). No hay un dominio de producción confirmado en el repo, así que se agregó `NEXT_PUBLIC_SITE_URL` (`.env.example`, default `http://localhost:3000`) en vez de adivinar una URL real. El sitio público es de una sola página, así que `sitemap.ts` lista exactamente una URL.

### TASK-055

🟢 Favicon / icon de marca

- Hallazgo: no existía ningún favicon — `GET /favicon.ico` devolvía 404 (único error de consola detectado por Lighthouse, tanto en dev como en build de producción). Agregado `app/icon.tsx` (convención de Next, genera el PNG vía `next/og`'s `ImageResponse`) con un monograma "CH" en los colores de marca — es un placeholder generado por código, no un asset de diseño; reemplazable cuando exista un logo real.

### TASK-056

🟢 Cabeceras de seguridad (CSP y afines)

- Hallazgo: auditoría "Best Practices" reportaba "No CSP found in enforcement mode" (severidad alta, informativo — no afectaba el score). Agregadas vía `next.config.ts::headers()`: `Content-Security-Policy` (con `connect-src` derivado de `NEXT_PUBLIC_API_URL` y `img-src https:` porque los logos/fotos de Client/TeamMember/Product son URLs externas provistas por el admin), `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`.

Auditoría Lighthouse (Chromium headless dentro del contenedor Docker, sin GPU) contra el build de producción, antes/después de TASK-053 a 056:

| Categoría | Antes | Después |
|---|---|---|
| Accessibility | 100 | 100 |
| SEO | 100 | 100 |
| Best Practices | 96 | 100 |
| Performance | 31 | 46 |

El único error de consola (favicon 404) desapareció. Performance/Core Web Vitals: el entorno de medición (headless sin GPU, con el throttling de CPU/red que aplica Lighthouse por defecto) no es representativo del hosting real (Vercel, ver DEPLOYMENT.md) — la mejora de 31→46 es real pero el número absoluto sigue inflado por el entorno. Las métricas de peso real (JS/CSS transferido, `unused-javascript` moderado, CLS=0) son razonables para una página sin librerías de UI adicionales. Recomendación: remedir con Lighthouse/PageSpeed Insights una vez desplegado en Vercel (TASK-034), en vez de seguir optimizando a ciegas contra un número que no es confiable en este entorno.

---

# PHASE 6 - Administration Panel

Nota: el backend ya expone las rutas `/admin/*` (TASK-032a). Lo pendiente
aquí es la UI de administración que las consuma.

- 🟢 Admin Login

- 🟢 Dashboard (shell mínimo)

- 🟢 CRUD Projects (API + UI: list/create/edit/delete)

- 🟢 CRUD Services (API + UI: list/create/edit/delete)

- 🟢 CRUD Technologies (API + UI: list/create/edit/delete)

- 🟢 CRUD Articles (API + UI: list/create/edit/delete)

- 🟢 CRUD Case Studies (API + UI: list/create/edit/delete)

---

# PHASE 7 - Consolidación de Arquitectura (CH-TECH V2)

Objetivo

Formalizar Clean Architecture (ADR-0012) antes de escalar el dominio. Es prerrequisito de la Fase 8: las entidades nuevas se construyen sobre la arquitectura objetivo, no sobre la estructura pragmática actual.

### TASK-037

🟢 Introducir `domain/` — entidades y value objects sin dependencias externas

### TASK-038

🟢 Introducir `application/` — puertos de repositorio y primer caso de uso de referencia

### TASK-039

🟢 Migrar el módulo `projects` (API + modelo existente) a la nueva estructura, como caso piloto

### TASK-040

🟢 Migrar los módulos restantes — un commit por módulo

- 🟢 `technologies`
- 🟢 `services`
- 🟢 `case_studies`
- 🟢 `articles`
- 🟢 `contact`
- 🟢 `auth`

---

# PHASE 8 - CH-TECH V2: Dominio de Empresa

Objetivo

Incorporar las entidades de negocio descritas en DATA_MODEL.md, construidas sobre la arquitectura de la Fase 7.

### TASK-041

🟢 Migraciones Alembic: `companies`, `team_members`, `service_lines`, `clients`, `testimonials`, `products`, `partners`

- `service_lines` incluye seed de las cinco líneas de negocio (VISION.md) como catálogo, no como contenido de negocio.
- Modelos SQLAlchemy y entidades `domain/` correspondientes ya existen; puertos/casos de uso/API quedan para TASK-043.

### TASK-042

🟢 Migraciones Alembic: extender `projects` (`client_id`), `services` (`service_line_id`), `contact_requests` (`interested_service_line_id`, `source`)

- Las tres columnas nuevas son nullable. `service_line_id` no se fuerza a NOT NULL todavía: hacerlo ahora habría requerido inventar un valor de relleno sin base real (ver DATABASE_SCHEMA.md "Restricciones"). Se endurece en una migración futura una vez exista UI de asignación (TASK-044).

### TASK-043

🟢 CRUD API de las entidades nuevas (pública + admin), según API.md

- Entidades cubiertas: `ServiceLine`, `Client`, `Partner`, `Testimonial`, `Product`, `TeamMember`, `Company` (singleton, sin POST/DELETE). Cada una sigue el patrón puerto/caso de uso/repositorio/schema/router de ADR-0012. Suite completa: 525 tests, 98.28% cobertura.

### TASK-044

🟢 CRUD Admin UI: Company (formulario único), Team, Clients, Testimonials, Products, Partners

- Cada entidad sigue el patrón list/new/[id]/edit + Form ya usado por Projects/Services (`FormData` sin librerías de formularios, tabla HTML simple, `useAuth().authedFetch`). Company es de un solo registro (`GET /company` público + `PUT /admin/company`, sin lista ni alta/baja). Client/Testimonial/Product/Partner no tienen lectura admin por id en API.md, así que su lista y su formulario de edición leen del mismo endpoint público de listado y filtran por id en el cliente. Suite completa: 133 tests, 56 archivos, todos en verde.

### TASK-045

🟢 Seed de datos iniciales: perfil de Company, founder como primer TeamMember, cinco ServiceLine

- Company (`seed_company`) y las cinco ServiceLine (migración `25679e647f10`, catálogo necesario per DATABASE_MIGRATIONS.md) ya existían desde TASK-042/043. Se agregó `seed_team`: crea a Yadzael Chalico como primer TeamMember, vinculado por `user_id` al admin sembrado por `seed_admin_user` (DATA_MODEL.md: el founder es quien tiene acceso al panel). Idempotente, corre en `main()` tras `seed_company`.

---

# PHASE 9 - CH-TECH V2: Landing de Empresa

Objetivo

Reemplazar la narrativa de portafolio personal por la de empresa en el sitio público.

### TASK-046

🟢 Hero de empresa (reemplaza mensaje centrado en el founder)

- `Hero` es ahora un Server Component async: usa `GET /company` para el headline/subtext (`tagline`/`mission`), con fallback estático (`lib/content/site.ts`) si la API falla o esos campos no están definidos — el hero nunca debe mostrar un estado de error, a diferencia del resto de secciones.

### TASK-047

🟢 Sección "Sobre CH-TECH" (reemplaza `About`)

- Mismo patrón que Hero: el párrafo introductorio viene de `Company.vision` (fallback estático), evitando repetir el mismo campo que Hero. Los 6 puntos diferenciadores se mantienen (ya eran válidos) pero reescritos en voz de empresa, sin primera persona. Ancla cambia de `#sobre-mi` a `#sobre-ch-tech`.

### TASK-048

🟢 Sección Líneas de negocio (reemplaza bloque genérico de Servicios)

- Nuevo componente `BusinessLines` consume `GET /service-lines` (las 5 líneas sembradas en TASK-042/045). Se eliminó `components/sections/Services.tsx` y su test, y `getServices()` de `lib/api/content.ts` (quedaba sin uso) — el `Service` genérico sigue existiendo en el backend y su admin CRUD, solo se retiró de la landing pública.

### TASK-049

🟢 Secciones Clientes y Testimonios

- `Clients` lista `GET /clients` completo (logo o nombre). `Testimonials` filtra a `featured=true` client-side (mismo criterio editorial que `Projects` con proyectos destacados).

### TASK-050

🟢 Sección Equipo

- Se agregó `getTeamMembers()` (`GET /team`, público, ya filtrado a `active=true` en el backend) a `lib/api/content.ts` — antes solo existía la variante admin autenticada. `Team` muestra nombre/rol/bio/foto/enlaces.

### TASK-051

🟢 Sección/página Productos SaaS (placeholder inicial)

- `Products` consume `GET /products`; si no hay productos (caso actual, sin seed de productos), muestra un placeholder de lista de espera con CTA a `#contacto` en vez de una sección vacía.

### TASK-052

🟢 Metadata SEO / Open Graph de marca de empresa

- La lógica vive en `lib/content/metadata.ts::buildMetadata()` (no en `app/layout.tsx` directamente) para poder probarla sin `next/font/google`, que `vitest.config.ts` ya excluye de testing. `generateMetadata` en `layout.tsx` solo delega. Título/descripción/OpenGraph se arman desde `Company.display_name`/`tagline`, con fallback estático.

Verificado extremo a extremo contra el backend real (`docker compose restart frontend` + `curl localhost:3000`): título, meta description y las 9 anclas nuevas/renombradas aparecen correctamente, incluyendo el founder sembrado en Equipo y las 5 líneas de negocio. Suite completa: 151 tests, 61 archivos, todos en verde. `tsc --noEmit` y `eslint .` limpios.