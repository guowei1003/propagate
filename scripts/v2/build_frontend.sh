#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR/frontend"

if [[ ! -d "node_modules" ]]; then
  "${ROOT_DIR}/scripts/v2/install_frontend.sh"
fi

npm run build

echo "前端构建完成：frontend/dist"
