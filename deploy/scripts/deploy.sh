#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

ENV="${1:-production}"

if [ "$ENV" = "dev" ]; then
    COMPOSE_FILE="$ROOT_DIR/deploy/docker-compose.dev.yml"
    echo "Deploying in DEV mode..."
elif [ "$ENV" = "production" ]; then
    COMPOSE_FILE="$ROOT_DIR/deploy/docker-compose.yml"
    echo "Deploying in PRODUCTION mode..."
else
    echo "Usage: $0 [dev|production]"
    exit 1
fi

if [ ! -f "$ROOT_DIR/.env" ]; then
    if [ -f "$ROOT_DIR/deploy/.env.example" ]; then
        echo "Creating .env from .env.example..."
        cp "$ROOT_DIR/deploy/.env.example" "$ROOT_DIR/.env"
    fi
fi

docker network create propagate-net 2>/dev/null || true

echo "Starting services..."
docker compose -f "$COMPOSE_FILE" up -d

echo ""
echo "Waiting for postgres..."
sleep 5

if [ "$ENV" = "production" ]; then
    echo "Initializing database..."
    "$SCRIPT_DIR/init_db.sh"
fi

echo ""
echo "=== Deployment complete ==="
echo "  Frontend: http://<your-server-ip>:8888"
echo "  API:      http://<your-server-ip>:8888/api  (internal: 8001)"
