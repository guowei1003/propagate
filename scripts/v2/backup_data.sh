#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

source "${ROOT_DIR}/scripts/v2/compose_helpers.sh"
export PROPAGATE_DATA_ROOT="${PROPAGATE_DATA_ROOT:-/data/propagate}"

APP_DATA="${PROPAGATE_DATA_ROOT}/app-data"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${PROPAGATE_DATA_ROOT}/backups/${STAMP}"
mkdir -p "$BACKUP_DIR"

if [[ -d "${APP_DATA}/bundles" ]]; then
  cp -R "${APP_DATA}/bundles" "${BACKUP_DIR}/bundles"
fi

if [[ -d "${APP_DATA}/runtime-v2" ]]; then
  cp -R "${APP_DATA}/runtime-v2" "${BACKUP_DIR}/runtime-v2"
fi

if command -v docker >/dev/null 2>&1; then
  propagate_v2_compose "$ROOT_DIR" exec -T postgres pg_dump -U postgres -d propagate > "${BACKUP_DIR}/propagate.sql"
fi

echo "备份完成：${BACKUP_DIR}"
