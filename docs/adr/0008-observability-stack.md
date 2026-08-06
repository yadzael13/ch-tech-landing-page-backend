# ADR-0008

## Título

Adoptar Uptime Kuma, Grafana y Prometheus como stack de observabilidad.

## Estado

Aceptado

## Fecha

2026-08-01

---

## Contexto

ROADMAP.md (Fase 4) requiere monitoring y observability. El proyecto es autohospedado en un VPS (backend), por lo que se prefieren herramientas open-source autohospedables sobre SaaS de pago.

---

## Decisión

- Uptime Kuma para monitoreo de disponibilidad (uptime/health checks externos).
- Grafana para dashboards.
- Prometheus para métricas (marcado como "futuro" en DEPLOYMENT.md — no bloquea el lanzamiento inicial).

---

## Alternativas

- Datadog / New Relic (SaaS, costo no justificado para un proyecto personal en esta etapa).
- Sentry únicamente (cubre error tracking, no reemplaza métricas de infraestructura).

---

## Consecuencias

### Positivas

- Costo cero, autohospedado, control total de los datos.
- Uptime Kuma tiene setup mínimo, valor inmediato desde el día uno.

### Negativas

- Mantenimiento propio de la infraestructura de observabilidad (a diferencia de un SaaS gestionado).
- Prometheus queda diferido; hasta su implementación, la observación de métricas de aplicación es limitada a logs (ver DOCKER.md).

---

## Referencias

https://github.com/louislam/uptime-kuma

https://grafana.com/docs/

https://prometheus.io/docs/
