#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="data/backups/${STAMP}"
mkdir -p "$BACKUP_DIR"

if [[ -d "data/bundles" ]]; then
  cp -R "data/bundles" "${BACKUP_DIR}/bundles"
fi

if [[ -d "data/runtime-v2" ]]; then
  cp -R "data/runtime-v2" "${BACKUP_DIR}/runtime-v2"
fi

if command -v docker >/dev/null 2>&1; then
  docker compose -f docker-compose.v2.yml exec -T postgres pg_dump -U postgres -d propagate > "${BACKUP_DIR}/propagate.sql"
fi

echo "备份完成：${BACKUP_DIR}"
