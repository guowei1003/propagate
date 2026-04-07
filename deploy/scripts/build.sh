#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Building Propagate ==="

echo "[1/3] Building Runner image..."
docker build -f "$ROOT_DIR/deploy/docker/runner.Dockerfile" -t propagate-runner:latest "$ROOT_DIR"

echo "[2/3] Building API image..."
docker build -f "$ROOT_DIR/deploy/docker/api.Dockerfile" -t propagate/api:latest "$ROOT_DIR/backend"

echo "[3/3] Building Frontend image..."
docker build -f "$ROOT_DIR/deploy/docker/frontend.Dockerfile" -t propagate/frontend:latest "$ROOT_DIR/frontend"

echo ""
echo "=== Build complete ==="
echo "  Runner:   propagate-runner:latest"
echo "  API:      propagate/api:latest"
echo "  Frontend: propagate/frontend:latest"
