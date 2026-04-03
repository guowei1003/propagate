#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "请先设置 DATABASE_URL" >&2
  exit 1
fi

PYTHON_BIN=".venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python"
fi

"$PYTHON_BIN" - <<'PY'
from pathlib import Path

import psycopg

from app.v2.core.config import v2_settings

sql = Path("migrations/002_v2_schema.sql").read_text(encoding="utf-8")
with psycopg.connect(v2_settings.database_url) as conn:
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
print("V2 migration applied.")
PY
