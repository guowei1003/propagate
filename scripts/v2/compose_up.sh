#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

source "${ROOT_DIR}/scripts/v2/compose_helpers.sh"
export PROPAGATE_DATA_ROOT="${PROPAGATE_DATA_ROOT:-/data/propagate}"

"${ROOT_DIR}/scripts/v2/ensure_propagate_data_root.sh"

propagate_v2_compose "$ROOT_DIR" up --build -d
propagate_v2_compose "$ROOT_DIR" ps

echo "V2 服务已启动。前端入口：http://127.0.0.1:8888/  API 文档：http://127.0.0.1:8888/docs"
