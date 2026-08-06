"""Rescata la estructura de la base de datos como SQL revisable.

Envuelve el modo offline de Alembic (`alembic upgrade head --sql`, que
`alembic/env.py::run_migrations_offline()` ya soporta sin cambios) para
producir un archivo .sql auditable con el DDL completo — la forma concreta
de "rescatar la estructura para replicar la base en MySQL" pedida en el plan
de migración, en vez de aplicar cambios a ciegas.

Uso:
    python scripts/migration_to_sql.py [--from <revision>] [--to <revision>]

Por defecto genera el rango completo `base:head`. El resultado se escribe en
`migration-review/<timestamp>_<rango>.sql` (gitignored) y también se imprime
por stdout.

El SQL generado debe revisarse y luego aplicarse SOLO con la credencial
chtech_migrator (MIGRATION_DATABASE_URL) — nunca con la credencial de la app
en ejecución (chtech_app/DATABASE_URL), que deliberadamente no tiene
privilegios DDL. Ver docs/adr/0001-mysql-database-privilege-separation.md.
"""

import argparse
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "migration-review"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from",
        dest="from_rev",
        default="base",
        help="Revisión de origen (default: base, es decir, esquema vacío).",
    )
    parser.add_argument(
        "--to",
        dest="to_rev",
        default="head",
        help="Revisión de destino (default: head).",
    )
    args = parser.parse_args()

    rev_range = f"{args.from_rev}:{args.to_rev}"
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_range = rev_range.replace(":", "-")
    output_file = OUTPUT_DIR / f"{timestamp}_{safe_range}.sql"

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", rev_range, "--sql"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        return result.returncode

    output_file.write_text(result.stdout, encoding="utf-8")
    print(result.stdout)
    print(f"\n-- SQL escrito en: {output_file}", file=sys.stderr)
    print(
        "-- Revisa este archivo, luego aplícalo SOLO con la credencial "
        "chtech_migrator (MIGRATION_DATABASE_URL):\n"
        "--   alembic upgrade head   (usa MIGRATION_DATABASE_URL automáticamente), o\n"
        "--   mysql -h <host> -u chtech_migrator -p chtech < "
        f"{output_file.name}\n"
        "-- Nunca con la credencial de la app (chtech_app/DATABASE_URL) — "
        "no tiene privilegios DDL a propósito.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
