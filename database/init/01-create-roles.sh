#!/bin/bash
# Bootstraps the two-credential privilege split described in
# docs/adr/0001-mysql-database-privilege-separation.md.
#
# chtech_app     — DML only (SELECT/INSERT/UPDATE/DELETE). Used by the
#                  running backend (DATABASE_URL). No CREATE/ALTER/DROP/
#                  INDEX — this is the concrete, DB-enforced guarantee that
#                  neither the app, the frontend, nor any AI assistant
#                  (coding-time or a future in-app feature) can alter table
#                  structure through the application's own DB connection.
# chtech_migrator — DDL (+ DML). Used ONLY by Alembic (MIGRATION_DATABASE_URL),
#                  run as an explicit CI/manual step — never by the running
#                  container's CMD in production (docs/DEPLOYMENT.md).
#
# Auto-executed by the official mysql image on first init
# (docker-entrypoint-initdb.d/*.sh), local/dev only. Production (RDS) has no
# such hook — see docs/DEPLOYMENT.md for the equivalent one-time manual step.
set -e

mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<-EOSQL
  CREATE USER IF NOT EXISTS 'chtech_app'@'%' IDENTIFIED BY '$MYSQL_APP_PASSWORD';
  GRANT SELECT, INSERT, UPDATE, DELETE ON \`$MYSQL_DATABASE\`.* TO 'chtech_app'@'%';

  CREATE USER IF NOT EXISTS 'chtech_migrator'@'%' IDENTIFIED BY '$MYSQL_MIGRATOR_PASSWORD';
  GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES
    ON \`$MYSQL_DATABASE\`.* TO 'chtech_migrator'@'%';

  -- Local/CI test database only (tests/conftest.py creates and tears down
  -- \`${MYSQL_DATABASE}_test\` per session — it needs the same DDL rights
  -- there as on the real schema). chtech_app is deliberately NOT granted
  -- anything here: it never runs tests directly against its own DML-only
  -- connection needing DDL.
  GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES
    ON \`${MYSQL_DATABASE}_test\`.* TO 'chtech_migrator'@'%';

  FLUSH PRIVILEGES;
EOSQL
