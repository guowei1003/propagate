#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"

curl -fsS "${API_BASE_URL}/healthz" >/dev/null
curl -fsS "${API_BASE_URL}/openapi.json" >/dev/null

echo "基础健康检查通过：${API_BASE_URL}"
