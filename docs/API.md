# API

## Objetivo

Este documento define el contrato REST de CH-TECH.

Representa el comportamiento esperado de la API antes de su implementación.

Todo endpoint implementado deberá respetar este contrato.

La especificación OpenAPI generada por FastAPI deberá mantenerse consistente con este documento.

---

# Base URL

Producción

/api/v1

Desarrollo

http://localhost:8000/api/v1

---

# Formato

Todas las peticiones y respuestas utilizan JSON.

Content-Type

application/json

---

# Versionado

Todas las rutas públicas deberán estar versionadas.

Ejemplo

/api/v1/projects

---

# Authentication

La API distingue dos tipos de acceso.

## Público

No requiere autenticación.

Ejemplos

GET /projects

GET /articles

GET /services

---

## Administrador

Requiere JWT.

Authorization

Bearer <token>

---

# Response Format

Todas las respuestas seguirán el mismo formato.

## Success

{
    "success": true,
    "data": {},
    "message": null
}

---

## Error

{
    "success": false,
    "error": {
        "code": "RESOURCE_NOT_FOUND",
        "message": "Project not found"
    }
}

---

# HTTP Status

200 OK

201 Created

204 No Content

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Validation Error

500 Internal Server Error

---

# Health

## GET /health

Descripción

Verifica el estado del sistema.

Autenticación

No requerida.

Respuesta

200

{
    "success": true,
    "data":
        {
            "status":true
        },
    "message": null
}



---

# Authentication

## POST /auth/login

Descripción

Inicia sesión como administrador.

Autenticación

No.

Body

{
    "email":"",
    "password":""
}

Respuesta

200

{
    "access_token":"",
    "refresh_token":"",
    "token_type":"Bearer"
}

Efecto

Crea un registro en `refresh_tokens` asociado al usuario (ver `DATABASE_SCHEMA.md`).

---

## POST /auth/refresh

Descripción

Renueva el access token utilizando un refresh token válido.

Autenticación

No (se valida el refresh token enviado, no el access token).

Body

{
    "refresh_token":""
}

Respuesta

200

{
    "access_token":"",
    "refresh_token":"",
    "token_type":"Bearer"
}

Efecto

Rotación: el refresh token recibido se marca como revocado (`revoked_at`) y se emite uno nuevo. Un refresh token ya usado o revocado no puede reutilizarse.

Errores

401 si el refresh token no existe, está expirado o ya fue revocado.

---

## POST /auth/logout

Descripción

Cierra la sesión actual.

Autenticación

Requiere JWT (access token).

Body

{
    "refresh_token":""
}

Respuesta

204

Efecto

Marca `revoked_at` en el registro correspondiente de `refresh_tokens`. El refresh token deja de poder usarse para renovar.

El access token en curso permanece técnicamente válido hasta su expiración natural (ver Token Lifetimes) — es stateless y no se puede invalidar sin mantener una lista de revocación adicional. Por eso su duración se mantiene corta.

---

## Token Lifetimes

Access Token

15 minutos. Stateless, firmado, no se persiste.

Refresh Token

7 días. Se persiste hasheado en `refresh_tokens`. Rotado en cada uso.

---

## GET /projects

Descripción

Obtiene proyectos públicos.

Autenticación

No.

Query Params

page

limit

technology

featured

status

search

Sort

created_at

title

Respuesta

200

{
    "success": true,
    "data": [
            {
                "id":"",
                "slug":"",
                "title":"",
                "featured":true
            }
        ],
    "message": null
}

---

GET /projects/{slug}

---

POST /admin/projects

---
PUT /admin/projects/{id}
---

DELETE /admin/projects/{id}

---

GET /technologies

---

GET /technologies/{id}

---

POST /admin/technologies

---

PUT /admin/technologies/{id}

---

DELETE /admin/technologies/{id}

---

GET /articles

---

GET /articles/{slug}

---

POST /admin/articles
---

PUT /admin/articles/{id}

---

DELETE /admin/articles/{id}

---

GET /services

---

GET /services/{slug}

---

POST /admin/services

---

PUT /admin/services/{id}

---

DELETE /admin/services/{id}

---

GET /case-studies

---

GET /case-studies/{id}

---

POST /admin/case-studies

---

PUT /admin/case-studies/{id}

---

DELETE /admin/case-studies/{id}

---

# CH-TECH V2 — Company

## GET /company

Descripción

Obtiene el perfil público de la empresa. Registro único.

Autenticación

No.

---

## PUT /admin/company

Descripción

Actualiza el perfil de la empresa. No existe `POST` ni `DELETE`: el registro es un singleton creado por seed/migración.

Autenticación

Requiere JWT.

---

# CH-TECH V2 — Team

GET /team

Solo devuelve miembros con `active = true` — igual que `active` en Service.

---

GET /team/{id}

Mismo filtro `active = true` que la lista pública; 404 si el miembro está inactivo.

---

GET /admin/team

Requiere JWT. Sin el filtro `active = true` — la tabla de administración necesita ver también a los miembros inactivos.

---

GET /admin/team/{id}

Requiere JWT. Sin el filtro `active = true` — permite cargar en el formulario de edición a un miembro inactivo que el endpoint público ocultaría.

---

POST /admin/team

---

PUT /admin/team/{id}

---

DELETE /admin/team/{id}

---

# CH-TECH V2 — Service Lines

GET /service-lines

---

GET /service-lines/{slug}

---

POST /admin/service-lines

---

PUT /admin/service-lines/{id}

---

DELETE /admin/service-lines/{id}

---

# CH-TECH V2 — Clients

GET /clients

---

POST /admin/clients

---

PUT /admin/clients/{id}

---

DELETE /admin/clients/{id}

---

# CH-TECH V2 — Testimonials

GET /testimonials

---

POST /admin/testimonials

---

PUT /admin/testimonials/{id}

---

DELETE /admin/testimonials/{id}

---

# CH-TECH V2 — Products

GET /products

---

GET /products/{slug}

---

POST /admin/products

---

PUT /admin/products/{id}

---

DELETE /admin/products/{id}

---

# CH-TECH V2 — Partners

GET /partners

---

POST /admin/partners

---

PUT /admin/partners/{id}

---

DELETE /admin/partners/{id}

---

POST /contact

{
    "name":"",

    "email":"",

    "company":"",

    "subject":"",

    "message":"",

    "interested_service_line_id":"",

    "source":""
}

{
    "message":"Contact request received."
}

`interested_service_line_id` y `source` son opcionales — el contrato original sigue siendo válido sin ellos (CH-TECH V2).

Efecto

Crea un `ContactRequest` con estado `NEW` y envía un email transaccional (Resend) al administrador notificando la nueva solicitud. El envío del email es asíncrono respecto a la respuesta HTTP: un fallo del proveedor de email no debe impedir que la solicitud quede registrada.

---

# Validation Rules

## Project

title

Obligatorio

Máximo 255 caracteres.

slug

Único.

description

Obligatorio.

---

## Contact

email

Debe ser válido.

message

Mínimo 20 caracteres.

Máximo 5000.

---

## Product — CH-TECH V2

name

Obligatorio.

slug

Único.

status

Obligatorio. Debe ser `WAITLIST`, `BETA` o `LIVE`.

---

## Company — CH-TECH V2

Solo existe un registro. `PUT /admin/company` opera siempre sobre ese único registro; no acepta un `id` en el path.

---

# Rate Limiting

POST /contact

10 requests/hour/IP

POST /auth/login

5 attempts/15 minutes

API Pública

100 requests/minute/IP

---

# OpenAPI

La documentación generada automáticamente por FastAPI (`/docs` y `/openapi.json`) es una representación técnica de esta API.

En caso de discrepancia, este documento define el contrato funcional y deberá actualizarse antes de modificar la implementación.

Toda modificación a un endpoint deberá reflejarse en:

- API.md
- Esquemas Pydantic
- OpenAPI
- Pruebas de integración