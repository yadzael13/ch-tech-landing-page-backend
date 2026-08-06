# ADR-0007

## Título

Adoptar Redis como store compartido para rate limiting.

## Estado

Aceptado

## Fecha

2026-08-01

---

## Contexto

API.md define límites de rate limiting concretos (ej. 5 intentos/15 min en login, 100 req/min en API pública). Un limitador en memoria de un solo proceso FastAPI no es válido si el backend corre con más de una réplica.

---

## Decisión

Se utiliza Redis como store compartido para los contadores de rate limiting. Redis no se usa para persistir sesiones (ver ADR de auth y DATABASE_SCHEMA.md, tabla `refresh_tokens`, que vive en la base de datos relacional — MySQL desde ADR-0014, originalmente PostgreSQL).

---

## Alternativas

- Rate limiting en memoria (no válido con múltiples réplicas).
- Rate limiting a nivel de Nginx/Cloudflare (complementario, no sustituye límites por-usuario definidos en la aplicación, ej. intentos de login).

---

## Consecuencias

### Positivas

- Funciona correctamente con múltiples réplicas del backend.
- Redis es rápido y con soporte nativo de expiración de claves (TTL), ideal para contadores de ventana deslizante.

### Negativas

- Introduce una dependencia de infraestructura adicional (otro servicio a operar/monitorear).

---

## Referencias

https://redis.io/docs/latest/develop/use/patterns/
