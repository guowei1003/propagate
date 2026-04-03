#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f ".venv/bin/python" ]]; then
  echo "未找到 .venv，请先运行 scripts/v2/bootstrap_backend.sh" >&2
  exit 1
fi

.venv/bin/python scripts/run_api.py
