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

# 持久化数据目录
DATA_DIR="/data/propagate"
COMPOSE_DIR="$DATA_DIR/compose"
DB_DIR="$DATA_DIR/db"
WEB_DIR="$DATA_DIR/web"

# 源码目录（项目根目录）
ROOT_DIR_REAL="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 创建目录结构
echo "Creating data directories..."
mkdir -p "$COMPOSE_DIR" "$DB_DIR" "$WEB_DIR"

# 复制配置文件
echo "Copying configuration files..."
cp "$COMPOSE_FILE" "$COMPOSE_DIR/docker-compose.yml"
cp "$ROOT_DIR_REAL/deploy/docker/nginx.conf" "$COMPOSE_DIR/web/nginx.conf" 2>/dev/null || true

if [ ! -f "$DATA_DIR/.env" ]; then
    if [ -f "$ROOT_DIR_REAL/deploy/.env.example" ]; then
        echo "Creating .env from .env.example..."
        cp "$ROOT_DIR_REAL/deploy/.env.example" "$DATA_DIR/.env"
    fi
fi

# 创建 docker network
docker network create propagate-net 2>/dev/null || true

# 从持久化目录启动服务（传递源码目录路径给 docker-compose）
cd "$COMPOSE_DIR"
echo "Starting services..."
ROOT_DIR="$ROOT_DIR_REAL" docker compose up -d

echo ""
echo "Waiting for postgres..."
sleep 5

if [ "$ENV" = "production" ]; then
    echo "Initializing database..."
    set -a
    source "$DATA_DIR/.env" 2>/dev/null || true
    set +a
    docker compose exec -T postgres psql -U postgres -d propagate <<-'EOF'
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    prompt TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS task_logs (
    id SERIAL PRIMARY KEY,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    message TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS task_results (
    id SERIAL PRIMARY KEY,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE UNIQUE,
    output TEXT,
    artifacts JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    llm_model VARCHAR(64) NOT NULL DEFAULT 'demo-heuristic',
    temperature FLOAT NOT NULL DEFAULT 0.2,
    timeout_sec INTEGER NOT NULL DEFAULT 300,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_task_logs_task_id ON task_logs(task_id);
EOF
    echo "Database initialized successfully."
fi

echo ""
echo "=== Deployment complete ==="
echo "  Data directory: $DATA_DIR"
echo "  Frontend:    http://<your-server-ip>:8888"
echo "  API:         http://<your-server-ip>:8888/api  (internal: 8001)"
