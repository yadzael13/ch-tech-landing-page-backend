# ADR-0011

## Título

Desplegar el backend en una instancia EC2 autogestionada (reemplaza App Runner, ADR-0010).

## Estado

Aceptado

## Fecha

2026-08-03

---

## Contexto

ADR-0010 puso el backend en AWS App Runner: serverless de un solo
contenedor por servicio, con TLS (ACM) y protección DDoS básica (AWS Shield
Standard) gestionados automáticamente, sin acceso al sistema operativo del
contenedor en ejecución.

El usuario decidió desplegar en instancias independientes en vez de un
servicio serverless: quiere el backend en una **instancia EC2** que él
mismo administra, con acceso directo al sistema operativo para instalar
Nginx y gestionar el certificado TLS con Let's Encrypt. La base de datos se
mantiene en **Amazon RDS** (decisión de ADR-0010, sin cambios) y el frontend
se mantiene en **Vercel** (ADR-0006, sin cambios) — este pivote afecta
únicamente al hosting del backend.

---

## Decisión

El backend corre en una instancia **EC2** con Docker Compose
(`docker-compose.prod.yml`), con dos servicios:

- `backend`: imagen construida por CI (`docker/backend/Dockerfile.prod`) y
  publicada en Amazon ECR (sin cambios respecto a ADR-0010).
- `redis`: vuelve a ser **self-hosted** en la misma instancia. App Runner
  obligaba a un servicio externo (Upstash, ADR-0010) por su límite de un
  solo contenedor por servicio; una EC2 con Docker Compose no tiene esa
  restricción, así que Redis puede volver a vivir junto al backend sin
  costo ni latencia de red adicional (ver ADR-0007).

**Nginx** corre containerizado delante del backend como reverse proxy
(`docker/nginx/nginx.conf`), terminando TLS con un certificado de **Let's
Encrypt** renovado vía certbot en el host (fuera de Docker), montado como
volumen de solo lectura dentro del contenedor de Nginx.

**Cloudflare** vuelve a colocarse delante del dominio del backend
(`api.ch-tech.dev`) en modo proxy, "Full (Strict)" — mismo rol que describía
ADR-0009 (protección DDoS/WAF básica y ocultamiento de la IP de la
instancia), ahora relevante otra vez porque App Runner (que incluía AWS
Shield Standard) deja de estar en el camino. ADR-0009 queda como registro
histórico de la decisión original y no se reescribe; esta ADR documenta la
reintroducción como una decisión nueva.

Las migraciones de Alembic siguen corriendo como paso explícito de CI antes
de actualizar la instancia (sin cambios respecto a ADR-0010) — ya no por
riesgo de instancias concurrentes autoescaladas (la EC2 es una sola
instancia), sino porque sigue siendo la forma más segura de aplicar cambios
de esquema antes de que el código nuevo empiece a servir tráfico.

El despliegue continuo pasa de "App Runner detecta el push a ECR
automáticamente" a un job explícito de GitHub Actions que usa **AWS Systems
Manager (SSM) Run Command** para instruir a la instancia EC2 a ejecutar
`docker compose pull && docker compose up -d`. Se prefiere sobre SSH porque
no requiere abrir el puerto 22 a internet ni guardar una clave privada como
secreto — mismo criterio que ya usa el repo al preferir OIDC sobre
credenciales de AWS de larga duración.

---

## Alternativas

- **Seguir en AWS App Runner** (ADR-0010): menos operación manual, pero sin
  acceso al sistema operativo — no permite instalar Nginx/certbot
  directamente, que es justo lo que el usuario quiere controlar.
- **AWS ECS (Fargate)**: ya considerada y descartada en ADR-0010 por
  sobredimensionada para un solo servicio backend; sigue sin elegirse aquí.
- **Redis administrado (Upstash/ElastiCache) en vez de self-hosted**: sigue
  siendo válido si en el futuro se agregan más instancias EC2 detrás de un
  balanceador (un Redis por-instancia dejaría de ser un store compartido
  válido, ver ADR-0007) — no es el caso mientras haya una sola instancia.

---

## Consecuencias

### Positivas

- Control total del sistema operativo de la instancia.
- Redis vuelve a ser gratuito y sin latencia de red externa.
- Sin el límite de "un solo contenedor por servicio" de App Runner.

### Negativas

- Vuelve la carga operativa manual: parches del sistema operativo,
  renovación del certificado de Let's Encrypt, y mantener Nginx
  actualizado — nada de esto lo gestiona AWS automáticamente como en App
  Runner.
- Cloudflare vuelve a ser una dependencia externa necesaria para
  DDoS/WAF/ocultar IP (ver ADR-0009), en vez de venir incluido como con AWS
  Shield Standard.
- Si en el futuro se necesita escalar a más de una instancia, Redis tendría
  que volver a salir de la instancia (mismo problema que resolvió ADR-0010
  con Upstash) y el despliegue vía SSM tendría que apuntar a varias
  instancias o a un Auto Scaling Group.

---

## Referencias

https://docs.aws.amazon.com/systems-manager/latest/userguide/execute-remote-commands.html

https://certbot.eff.org/instructions
