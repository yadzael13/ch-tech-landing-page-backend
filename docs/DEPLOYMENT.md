# Deployment Strategy

## Development

Docker Compose

## Staging

Docker Compose sobre VPS.

## Production

Frontend

Vercel

Backend

Instancia EC2 autogestionada (ver ADR-0011), Docker Compose (`docker-compose.prod.yml`): servicios `backend` (imagen desde Amazon ECR) y `redis`.

Nginx (containerizado) como reverse proxy delante del backend, con TLS de Let's Encrypt (certbot en el host, certificado montado como volumen de solo lectura).

Cloudflare delante del dominio del backend, modo proxy Full (Strict) — protección DDoS/WAF básica y ocultamiento de la IP de la instancia.

Migraciones de Alembic corren como paso explícito de CI antes de actualizar la instancia, nunca en el `CMD` del contenedor, usando la credencial `chtech_migrator` (`MIGRATION_DATABASE_URL`) — nunca la credencial de la app en ejecución.

`app/db/purge_refresh_tokens.py` corre vía cron en el host (diario), fuera de Docker Compose: `docker compose exec -T backend python -m app.db.purge_refresh_tokens` (ver DATABASE_SCHEMA.md "refresh_tokens" — Retención).

Despliegue vía AWS Systems Manager (SSM) Run Command desde GitHub Actions — sin SSH expuesto ni claves privadas como secreto.

Database

Amazon RDS para MySQL (o Aurora MySQL) — ver ADR-0014 (migrado desde PostgreSQL, ADR-0010).

Backups automáticos gestionados por RDS.

TLS en producción: a diferencia de `asyncpg` (que aceptaba `?ssl=require` como parámetro de la URL de conexión), `aiomysql`/PyMySQL requieren pasar el contexto TLS vía `connect_args` de SQLAlchemy (`create_async_engine(url, connect_args={"ssl": {...}})`), no como query string. En desarrollo (MySQL self-hosted vía Docker Compose, misma red interna) no hace falta.

Privilegios de base de datos: RDS no tiene un hook de inicialización equivalente a `docker-entrypoint-initdb.d` (ver `database/init/01-create-roles.sh`, usado en desarrollo). El bootstrap de `chtech_app` (DML) y `chtech_migrator` (DDL) sobre la instancia RDS es un paso manual, único, que se ejecuta una sola vez al aprovisionar la base de datos, conectando con la credencial maestra de RDS y ejecutando el mismo `CREATE USER` / `GRANT` que el script de desarrollo (ver ADR-0014). No forma parte de ningún pipeline automatizado.

Cache / Rate Limiting

Redis self-hosted en la misma instancia EC2 (ver ADR-0011)

## Monitoring

Uptime Kuma

Grafana

Prometheus (futuro)

## Logs

Docker Logs

Rotación automática.

## Notifications

Resend

Envío de email transaccional al administrador cuando se recibe un nuevo `ContactRequest`.