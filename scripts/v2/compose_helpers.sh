#!/usr/bin/env bash
# shellcheck shell=bash
# 由 scripts/v2 下其它脚本 source：统一 PROPAGATE_DATA_ROOT 与 docker compose 调用。

propagate_v2_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

propagate_v2_compose() {
  local root="${1:-$propagate_v2_repo_root}"
  shift
  export PROPAGATE_DATA_ROOT="${PROPAGATE_DATA_ROOT:-/data/propagate}"
  local env_file="${PROPAGATE_DATA_ROOT}/config/.env"
  local cmd=(docker compose -f docker-compose.v2.yml)
  if [[ -f "$env_file" ]]; then
    cmd+=(--env-file "$env_file")
  fi
  (cd "$root" && "${cmd[@]}" "$@")
}
