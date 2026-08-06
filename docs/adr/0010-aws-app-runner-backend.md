# ADR-0010

## Título

Desplegar el backend en AWS App Runner (reemplaza el VPS autogestionado).

## Estado

Reemplazada por ADR-0011

> El backend deja AWS App Runner por una instancia EC2 autogestionada
> (ADR-0011) — el usuario decidió desplegar en instancias independientes en
> vez de un servicio serverless, para tener acceso directo al sistema
> operativo (Nginx + Let's Encrypt propios). La decisión de base de datos
> (Amazon RDS) de esta ADR no cambia. Se conserva como registro histórico de
> la decisión original, no se reescribe.

## Fecha

2026-08-03

---

## Contexto

ADR-0009 y `DEPLOYMENT.md` planeaban un VPS Ubuntu autogestionado para el
backend: Docker + Nginx como reverse proxy + Let's Encrypt para el
certificado de origen + Cloudflare delante en modo proxy. Nunca se llegó a
contratar ese VPS ni el dominio asociado — el usuario decidió desplegar en
AWS en su lugar, antes de invertir en esa infraestructura.

App Runner es un servicio *serverless de un solo contenedor por servicio*:
recibe una imagen (de Amazon ECR) o el código fuente, y administra TLS,
dominio, autoescalado y balanceo de carga sin que haya que configurar red
(VPC), un load balancer o un clúster a mano.

---

## Decisión

El backend se despliega en **AWS App Runner**, a partir de una imagen
construida por CI (`docker/backend/Dockerfile.prod`) y publicada en
**Amazon ECR**. La base de datos pasa a **Amazon RDS para PostgreSQL**. El
store de Redis (usado únicamente para rate limiting, ver ADR-0007) pasa a
**Upstash Redis** — App Runner no permite un segundo contenedor en el mismo
servicio, así que Redis debe ser un servicio administrado externo de
cualquier forma; Upstash tiene capa gratuita y es compatible por URL
estándar (`rediss://`) sin cambiar `backend/app/core/rate_limit.py`.
ElastiCache queda como alternativa "100% AWS" si se prefiere, a costo mayor
(sin capa gratuita).

Las migraciones de Alembic **no** corren automáticamente al arrancar el
contenedor (a diferencia de `Dockerfile.dev`): App Runner puede levantar
varias instancias a la vez por autoescalado, y correr `alembic upgrade head`
en el `CMD` de cada una arriesga una carrera entre instancias contra la
misma base. Las migraciones corren como paso explícito y separado (ej. un
job de CI) antes de actualizar el servicio.

---

## Alternativas

- **VPS Ubuntu autogestionado** (plan original, ADR-0009): más control,
  pero requiere mantener Nginx, renovación de certificados y parches del
  sistema operativo a mano — carga operativa que no se justifica para un
  proyecto personal de bajo tráfico.
- **AWS ECS (Fargate)**: más control de red y más servicios simultáneos,
  pero exige armar clúster, task definitions, Application Load Balancer y
  VPC/subnets a mano — sobredimensionado para un solo servicio backend.
- **AWS Elastic Beanstalk**: soporta Docker con menos configuración manual
  que ECS, pero con más "magia"/menos control que App Runner y menos
  alineado con el modelo de un solo contenedor que ya usa el proyecto.

---

## Consecuencias

### Positivas

- TLS y certificado gestionados automáticamente (AWS Certificate Manager) —
  ya no hace falta Nginx ni renovar Let's Encrypt a mano.
- Protección DDoS básica incluida (AWS Shield Standard) — Cloudflare deja de
  ser necesario para ese propósito (ver ADR-0009, marcada como reemplazada).
- Autoescalado gestionado, sin clúster ni load balancer que mantener a mano.

### Negativas

- Redis deja de poder vivir junto al backend — dependencia externa
  adicional (Upstash o ElastiCache) con su propio costo/latencia de red.
- RDS tiene costo real desde el día uno (sin capa gratuita permanente, solo
  12 meses de prueba en cuentas nuevas) — más caro que un Postgres
  autohospedado en un VPS pequeño.
- El autoescalado de App Runner obliga a tratar las migraciones como un
  paso de despliegue separado, no como parte del arranque del contenedor —
  más piezas móviles en el pipeline de CI/CD que con un solo VPS.
- Nuevo punto de dependencia en el ecosistema de AWS (ECR, RDS, IAM/OIDC)
  en vez de una sola VM — más superficie de configuración de permisos.

---

## Referencias

https://docs.aws.amazon.com/apprunner/latest/dg/what-is-apprunner.html

https://upstash.com/docs/redis/overall/getstarted
