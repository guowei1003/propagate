#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

COMPOSE_FILE="${ROOT_DIR}/deploy/docker-compose.yml"
BASE_DIR="${PROPAGATE_BASE_DIR:-/data/propagate}"
ENV_FILE=""
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-propagate}"

usage() {
  cat <<'EOF'
用法:
  bash ./dev.sh [选项]

选项:
      --base-dir <目录>      基础数据目录，默认 /data/propagate
      --env-file <文件>      配置文件路径，默认 <base-dir>/config/propagate.env
      --compose-file <文件>  Compose 文件，默认 deploy/docker-compose.yml
      --project-name <名称>  Compose project name，默认 propagate
  -h, --help                显示帮助
EOF
}

log() {
  printf '[dev-deploy] %s\n' "$*"
}

resolve_compose_cmd() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
    return
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
    return
  fi

  printf '缺少 docker compose 或 docker-compose\n' >&2
  exit 1
}

write_default_env() {
  local env_file="$1"
  local config_dir="$2"
  local postgres_dir="$3"
  local app_data_dir="$4"

  cat > "$env_file" <<EOF
COMPOSE_PROJECT_NAME=${PROJECT_NAME}
POSTGRES_DB=propagate
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
PROPAGATE_DEFAULT_PROVIDER=mock
PROPAGATE_DEFAULT_MODEL=gpt-4.1-mini
PROPAGATE_OPENAI_API_KEY=
PROPAGATE_OPENAI_BASE_URL=https://api.openai.com/v1
PROPAGATE_POSTGRES_DIR=${postgres_dir}
PROPAGATE_APP_DATA_DIR=${app_data_dir}
PROPAGATE_CONFIG_DIR=${config_dir}
PROPAGATE_ARTIFACTS_DIR=/app/data/artifacts
PROPAGATE_WORKSPACES_DIR=/app/data/workspaces
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-dir)
      BASE_DIR="${2:-}"
      shift 2
      ;;
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --compose-file)
      COMPOSE_FILE="${2:-}"
      shift 2
      ;;
    --project-name)
      PROJECT_NAME="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf '未知参数: %s\n' "$1" >&2
      usage
      exit 1
      ;;
  esac
done

resolve_compose_cmd

if [[ "$BASE_DIR" != /* ]]; then
  BASE_DIR="${ROOT_DIR}/${BASE_DIR}"
fi

if [[ "$COMPOSE_FILE" != /* ]]; then
  COMPOSE_FILE="${ROOT_DIR}/${COMPOSE_FILE}"
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  printf 'Compose 文件不存在: %s\n' "$COMPOSE_FILE" >&2
  exit 1
fi

if [[ -z "$ENV_FILE" ]]; then
  ENV_FILE="${BASE_DIR}/config/propagate.env"
fi

if [[ "$ENV_FILE" != /* ]]; then
  ENV_FILE="${ROOT_DIR}/${ENV_FILE}"
fi

ENV_DIR="$(mkdir -p "$(dirname "$ENV_FILE")" && cd "$(dirname "$ENV_FILE")" && pwd)"
ENV_FILE="${ENV_DIR}/$(basename "$ENV_FILE")"

DEFAULT_POSTGRES_DIR="${BASE_DIR}/postgres"
DEFAULT_APP_DATA_DIR="${BASE_DIR}/app"
DEFAULT_CONFIG_DIR="$(dirname "$ENV_FILE")"

if [[ ! -f "$ENV_FILE" ]]; then
  log "初始化配置文件: ${ENV_FILE}"
  write_default_env "$ENV_FILE" "$DEFAULT_CONFIG_DIR" "$DEFAULT_POSTGRES_DIR" "$DEFAULT_APP_DATA_DIR"
fi

set -a
. "$ENV_FILE"
set +a

POSTGRES_DIR="${PROPAGATE_POSTGRES_DIR:-$DEFAULT_POSTGRES_DIR}"
APP_DATA_DIR="${PROPAGATE_APP_DATA_DIR:-$DEFAULT_APP_DATA_DIR}"
CONFIG_DIR="${PROPAGATE_CONFIG_DIR:-$DEFAULT_CONFIG_DIR}"

mkdir -p "$POSTGRES_DIR" "$APP_DATA_DIR" "$APP_DATA_DIR/artifacts" "$APP_DATA_DIR/workspaces" "$CONFIG_DIR"

export COMPOSE_PROJECT_NAME="${PROJECT_NAME:-${COMPOSE_PROJECT_NAME:-propagate}}"
export PROPAGATE_POSTGRES_DIR="$POSTGRES_DIR"
export PROPAGATE_APP_DATA_DIR="$APP_DATA_DIR"
export PROPAGATE_CONFIG_DIR="$CONFIG_DIR"

log "compose file: ${COMPOSE_FILE}"
log "env file: ${ENV_FILE}"
log "postgres dir: ${POSTGRES_DIR}"
log "app data dir: ${APP_DATA_DIR}"
log "config dir: ${CONFIG_DIR}"
log "project name: ${COMPOSE_PROJECT_NAME}"

cd "$ROOT_DIR"

log "开始构建镜像"
"${COMPOSE_CMD[@]}" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" build

log "启动 compose 服务"
"${COMPOSE_CMD[@]}" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" up -d

log "部署完成"
