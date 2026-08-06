# Docker

## Objetivo

Todo el desarrollo de CH-TECH se realizará mediante Docker.

No se instalarán dependencias del proyecto directamente en el sistema operativo.

---

## Servicios

Este repositorio (backend) no incluye el servicio `frontend` — el frontend
vive en `ch-tech-landing-page-frontend`, un repositorio separado, y corre
de forma independiente (`npm run dev`) contra la URL de este backend. Ver
`docs/adr/0014-mysql-database-privilege-separation.md` y el `README.md`
raíz para el detalle de la separación.

Backend

FastAPI

Puerto 8000

Database

MySQL 8.4 (migrado desde PostgreSQL — ver ADR-0014)

Puerto 3306

Redis

Puerto 6379

---

## Base de datos de pruebas

Los tests de backend (`pytest`) nunca corren contra la base de datos que usa
el backend en ejecución. Usan una base separada, `<MYSQL_DATABASE>_test` en el
mismo servidor MySQL, creada automáticamente en la primera ejecución con la
credencial `chtech_migrator` (ver ADR-0014 — los tests son la única
excepción documentada a que `chtech_app` nunca vea privilegios DDL).

Cada test crea su esquema desde cero y lo destruye al terminar
(`Base.metadata.create_all` / `drop_all`) — hacerlo contra la base real del
backend en ejecución la dejaría sin tablas. Ver `tests/conftest.py`.

---

## Comandos

Levantar

docker compose up

Reconstruir

docker compose up --build

Detener

docker compose down

Entrar al backend

docker compose exec backend bash

Ver logs

docker compose logs -f

Reconstruir un servicio

docker compose build backend

---

## Docker Compose

Backend

Database

Redis

---

## Production

Docker

Backend

Redis

Nginx Reverse Proxy

(Database en producción es Amazon RDS, fuera de Docker Compose — ver DEPLOYMENT.md)