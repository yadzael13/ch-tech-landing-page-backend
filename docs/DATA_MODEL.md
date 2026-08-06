# Data Model

## Objetivo

Este documento describe el dominio de CH-TECH.

No representa el esquema físico de la base de datos.

Las entidades aquí descritas representan el lenguaje del negocio.

---

# Principios

- El modelo debe ser independiente del ORM.
- No se describen tablas SQL.
- No se describen migraciones.
- Las relaciones representan reglas de negocio.
- Toda entidad deberá tener identificador único.
- Toda entidad deberá registrar auditoría (created_at, updated_at).

---

## User

Representa un administrador del sistema.

### Responsabilidades

- Autenticarse.
- Administrar contenido.
- Publicar proyectos.
- Publicar artículos.
- Gestionar servicios.

### Atributos

- id
- name
- email
- password_hash
- role
- is_active
- last_login
- created_at
- updated_at

### Relaciones

Puede crear:

- Projects
- Articles
- Case Studies

Tiene muchos:

- RefreshTokens

Puede estar asociado a un TeamMember (perfil público mostrado en la landing).

---

## RefreshToken

Representa una sesión de autenticación activa de un administrador.

Permite renovar el access token sin reautenticar, y revocar una sesión de forma explícita (logout) o forzada (ej. cambio de contraseña).

### Responsabilidades

- Permitir renovar el access token.
- Permitir invalidar una sesión.
- Registrar el origen de la sesión (dispositivo/IP) para auditoría.

### Atributos

- id
- user_id
- token_hash
- issued_at
- expires_at
- revoked_at
- user_agent
- ip_address

### Reglas

- El valor del refresh token nunca se persiste en texto plano; solo su hash.
- Un refresh token se usa una única vez: cada `POST /auth/refresh` revoca el token actual y emite uno nuevo (rotación).
- `revoked_at` distingue una sesión cerrada (logout, rotación, o revocación forzada) de una simplemente expirada.

### Relaciones

Pertenece a un User.

---

## Company — NUEVO (CH-TECH V2)

Representa el perfil público de la empresa. Registro único (singleton), no una lista.

### Responsabilidades

- Centralizar los datos de marca mostrados en la landing (nombre, tagline, misión, visión, contacto corporativo).
- Servir como fuente de verdad para el contenido hoy hardcodeado en el componente `About`.

### Atributos

- id
- legal_name
- display_name
- tagline
- mission
- vision
- email
- phone
- address
- social_links
- created_at
- updated_at

### Reglas

- Solo existe un registro. La API expone `GET /company` sin parámetros y `PUT /admin/company` (no hay `POST` ni `DELETE`).

---

## TeamMember — NUEVO (CH-TECH V2)

Representa a una persona del equipo mostrada públicamente. El founder (Yadzael Chalico, "Founder & Lead Software Engineer") es el primer registro.

### Responsabilidades

- Mostrar quién forma parte de CH-TECH.

### Atributos

- id
- user_id (opcional)
- name
- role
- bio
- photo
- linkedin_url
- github_url
- display_order
- active
- created_at
- updated_at

### Relaciones

Puede estar asociado a un User, si esa persona tiene acceso al panel administrativo. No todo TeamMember requiere una cuenta.

---

## ServiceLine — NUEVO (CH-TECH V2)

Representa una de las cinco líneas de negocio de CH-TECH: Software Engineering, AI & Automation, Digital Solutions, SaaS Products, Technology Consulting.

### Responsabilidades

- Agrupar los Services ofrecidos bajo una categoría de negocio coherente.
- Permitir que un ContactRequest indique en qué línea está interesado.

### Atributos

- id
- slug
- name
- description
- icon
- display_order
- created_at
- updated_at

### Relaciones

Muchos Services.

Muchos ContactRequests (interés declarado).

---

## Project

Representa un proyecto desarrollado por CH-TECH.

Puede ser:

- SaaS
- Open Source
- Cliente
- Personal
- Experimental

### Atributos

- id
- slug
- title
- short_description
- full_description
- repository_url
- live_demo_url
- cover_image
- status
- visibility
- featured
- client_id (opcional — CH-TECH V2)
- started_at
- finished_at
- created_at
- updated_at

### Relaciones

Muchos Technologies

Muchos CaseStudies

Pertenece opcionalmente a un Client (CH-TECH V2) — un proyecto propio (SaaS, Open Source, Personal) no tiene cliente asociado.

---

## Technology

Representa una tecnología utilizada.

Ejemplos

- Python
- FastAPI
- Docker
- MySQL

### Atributos

- id
- name
- category
- icon
- official_url
- created_at
- updated_at

### Relaciones

Muchos Projects

Muchos Articles

---

## Service

Representa un servicio profesional ofrecido, perteneciente a una línea de negocio.

Ejemplos

- Automatización IA
- Desarrollo Web
- Consultoría
- APIs

### Atributos

- id
- service_line_id (CH-TECH V2 — regla de negocio: todo servicio pertenece a una línea. Nullable en el esquema físico hasta que exista una UI de asignación — ver DATABASE_SCHEMA.md)
- title
- slug
- description
- featured
- active
- created_at
- updated_at

### Relaciones

Pertenece a una ServiceLine (CH-TECH V2).

---

## Article

Representa una publicación técnica.

### Atributos

- id
- slug
- title
- summary
- content
- cover_image
- published
- published_at
- reading_time
- created_at
- updated_at

### Relaciones

Muchas Technologies

Autor User

---

## CaseStudy

Representa el análisis técnico de un proyecto.

### Atributos

- id
- project_id
- challenge
- solution
- architecture
- lessons_learned
- metrics
- created_at
- updated_at

### Relaciones

Pertenece a un Project.

---

## Client — NUEVO (CH-TECH V2)

Representa una empresa u organización cliente de CH-TECH.

### Responsabilidades

- Mostrar qué empresas confían en CH-TECH.
- Servir de referencia para Projects y Testimonials.

### Atributos

- id
- name
- logo
- industry
- website_url
- created_at
- updated_at

### Relaciones

Muchos Projects.

Muchos Testimonials.

---

## Testimonial — NUEVO (CH-TECH V2)

Representa una cita de un cliente sobre el trabajo de CH-TECH.

### Responsabilidades

- Aportar prueba social en la landing.

### Atributos

- id
- author_name
- author_role
- client_id (opcional)
- project_id (opcional)
- content
- rating (opcional)
- featured
- created_at
- updated_at

### Relaciones

Pertenece opcionalmente a un Client.

Pertenece opcionalmente a un Project.

---

## Product — NUEVO (CH-TECH V2)

Representa un producto SaaS propio de CH-TECH en el catálogo público.

Es exclusivamente un registro de catálogo — ver ADR-0013. No almacena tenants, usuarios finales, planes ni facturación; eso vive en el backend propio de cada producto.

### Responsabilidades

- Mostrar el catálogo de productos SaaS de CH-TECH en la landing.
- Enlazar al dominio propio de cada producto (`url`), no alojarlo.

### Atributos

- id
- slug
- name
- short_description
- full_description
- status
- url
- logo
- featured
- created_at
- updated_at

---

## Partner — NUEVO (CH-TECH V2)

Representa una alianza tecnológica o de negocio de CH-TECH.

### Atributos

- id
- name
- logo
- partnership_type
- website_url
- created_at
- updated_at

---

## ContactRequest

Representa una solicitud enviada desde el formulario de contacto. Extendida en CH-TECH V2 con contexto comercial, sin romper el contrato existente de `POST /contact` — los campos nuevos son opcionales (ver ADR de decisión en el análisis de CH-TECH V2 y API.md).

### Atributos

- id
- name
- email
- company
- subject
- message
- interested_service_line_id (opcional — CH-TECH V2)
- source (opcional — CH-TECH V2, ej. "landing_form", "referral")
- status
- created_at

### Relaciones

Pertenece opcionalmente a una ServiceLine (CH-TECH V2).

### Estados

NEW

READ

REPLIED

ARCHIVED

---

## Value Objects

Email

Slug

Url

Image

Password

MarkdownContent

---

## ProjectStatus

PLANNING

IN_PROGRESS

COMPLETED

ARCHIVED

---

## Visibility

PUBLIC

PRIVATE

---

## ContactStatus

NEW

READ

REPLIED

ARCHIVED

---

## ProductStatus — NUEVO (CH-TECH V2)

WAITLIST

BETA

LIVE

---

## UserRole

ADMIN
