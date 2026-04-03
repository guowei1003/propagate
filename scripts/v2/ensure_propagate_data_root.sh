#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROPAGATE_DATA_ROOT="${PROPAGATE_DATA_ROOT:-/data/propagate}"

if ! mkdir -p "${PROPAGATE_DATA_ROOT}" 2>/dev/null; then
  echo "无法创建或访问 ${PROPAGATE_DATA_ROOT}。请使用有权限的用户执行，或设置 PROPAGATE_DATA_ROOT 指向可写目录。" >&2
  exit 1
fi

for sub in postgres app-data config backups; do
  mkdir -p "${PROPAGATE_DATA_ROOT}/${sub}"
done

ENV_DST="${PROPAGATE_DATA_ROOT}/config/.env"
ENV_SRC_EX="${ROOT_DIR}/.env.example"
if [[ ! -f "$ENV_DST" ]] && [[ -f "$ENV_SRC_EX" ]]; then
  cp "$ENV_SRC_EX" "$ENV_DST"
  echo "已创建 ${ENV_DST}（自 .env.example 复制）。请按需编辑后再启动。"
fi

echo "Propagate 数据根目录就绪：${PROPAGATE_DATA_ROOT}"
echo "  - postgres -> ${PROPAGATE_DATA_ROOT}/postgres"
echo "  - app 数据 -> ${PROPAGATE_DATA_ROOT}/app-data（对应容器内 /app/data）"
echo "  - 可选配置 -> ${PROPAGATE_DATA_ROOT}/config/.env（存在时 compose_up 会自动 --env-file）"
echo "  - 备份输出 -> ${PROPAGATE_DATA_ROOT}/backups"
