#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "用法：scripts/v2/package_bundle.sh <RUN_ID>" >&2
  exit 1
fi

RUN_ID="$1"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PROPAGATE_DATA_ROOT="${PROPAGATE_DATA_ROOT:-/data/propagate}"
APP_DATA="${PROPAGATE_DATA_ROOT}/app-data"
BUNDLE_DIR="${APP_DATA}/bundles/${RUN_ID}"
ARCHIVE_PATH="${APP_DATA}/bundles/${RUN_ID}.tar.gz"

if [[ ! -d "$BUNDLE_DIR" ]]; then
  echo "未找到 bundle 目录：$BUNDLE_DIR" >&2
  exit 1
fi

tar -czf "$ARCHIVE_PATH" -C "${APP_DATA}/bundles" "$RUN_ID"

echo "打包完成：$ARCHIVE_PATH"
