#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

COMPOSE_FILE="${1:-$ROOT_DIR/deploy/docker-compose.yml}"
SERVICE="${2:-}"

if [ -n "$SERVICE" ]; then
    echo "Restarting service: $SERVICE"
    docker compose -f "$COMPOSE_FILE" restart "$SERVICE"
else
    echo "Restarting all services..."
    docker compose -f "$COMPOSE_FILE" restart
fi
