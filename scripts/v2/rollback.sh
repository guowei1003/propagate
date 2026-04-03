#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

source "${ROOT_DIR}/scripts/v2/compose_helpers.sh"
export PROPAGATE_DATA_ROOT="${PROPAGATE_DATA_ROOT:-/data/propagate}"

propagate_v2_compose "$ROOT_DIR" down

echo "已停止当前 V2 服务。请按你的镜像/分支策略切回上一版本后重新启动。"
