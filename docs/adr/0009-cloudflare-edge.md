# ADR-0009

## Título

Adoptar Cloudflare como capa de DNS/proxy delante del backend.

## Estado

Reemplazada por ADR-0010

> El backend deja el VPS Ubuntu autogestionado por AWS App Runner
> (ADR-0010), que ya incluye TLS gestionado (ACM) y protección DDoS básica
> (AWS Shield Standard) — Cloudflare deja de ser necesario para el propósito
> que motivó esta ADR. Se conserva como registro histórico de la decisión
> original, no se reescribe.

## Fecha

2026-08-01

---

## Contexto

El frontend en Vercel ya cuenta con CDN propio. El backend corre en un VPS Ubuntu con IP pública expuesta directamente vía Nginx — sin protección DDoS/WAF ni ocultamiento de la IP de origen.

---

## Decisión

Cloudflare gestiona el DNS del dominio del backend (`api.ch-tech.dev`) en modo proxy (naranja), en modo "Full (Strict)" — valida el certificado de origen emitido por Let's Encrypt en el VPS. Cloudflare no se usa delante del frontend (Vercel ya provee su propio edge).

---

## Alternativas

- Exponer el VPS directamente sin proxy (más simple, sin protección DDoS/WAF, IP de origen expuesta).
- AWS CloudFront / otro CDN (mayor costo y complejidad para el alcance actual).

---

## Consecuencias

### Positivas

- Protección DDoS/WAF básica sin costo adicional.
- Oculta la IP real del VPS.
- Complementa, no reemplaza, el certificado de origen (Let's Encrypt sigue siendo necesario en modo Full Strict).

### Negativas

- Punto de dependencia adicional: si Cloudflare tiene una interrupción, el backend deja de ser alcanzable pese a estar operativo.
- Requiere mantener sincronizados los certificados de origen y la configuración de Cloudflare.

---

## Referencias

https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/
