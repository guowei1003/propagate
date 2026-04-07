#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Cleaning up Propagate ==="

echo "Stopping and removing containers..."
docker compose -f "$ROOT_DIR/deploy/docker-compose.yml" down 2>/dev/null || true
docker compose -f "$ROOT_DIR/deploy/docker-compose.dev.yml" down 2>/dev/null || true

echo "Removing volumes..."
docker compose -f "$ROOT_DIR/deploy/docker-compose.yml" down -v 2>/dev/null || true
docker compose -f "$ROOT_DIR/deploy/docker-compose.dev.yml" down -v 2>/dev/null || true

echo "Removing images..."
docker rmi propagate-runner:latest 2>/dev/null || true
docker rmi propagate/api:latest 2>/dev/null || true
docker rmi propagate/frontend:latest 2>/dev/null || true

echo "Removing network..."
docker network rm propagate-net 2>/dev/null || true

echo "Clean complete."
