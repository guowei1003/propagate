#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR/frontend"

REGISTRY="${NPM_REGISTRY:-https://registry.npmjs.org/}"
npm install --registry="$REGISTRY"

echo "前端依赖安装完成。"
