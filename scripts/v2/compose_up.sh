#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

docker compose -f docker-compose.v2.yml up --build -d

docker compose -f docker-compose.v2.yml ps

echo "V2 服务已启动。前端入口：http://127.0.0.1:8080  API 文档：http://127.0.0.1:8000/docs"
