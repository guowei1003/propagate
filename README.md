# Propagate

Propagate V2 is a controlled AI task execution system with a FastAPI backend, PostgreSQL-oriented V2 data model, Docker-first runtime planning, capability approval flow, bundle delivery, and a React/Vite/TypeScript SPA scaffold.

## V2 Features

- `/v2/tasks` task creation, requirement persistence, clarification rounds, and subtask materialization
- `/v2/capabilities` agent/skill candidate generation, risk scoring, approval, and rejection
- `/v2/env-profiles` environment profile management with stage-specific model routing
- `/v2/runs/{id}/resume` run recovery and execution evidence collection
- `/v2/runs/{id}/bundle` bundle manifest generation and artifact indexing
- React/Vite/TypeScript frontend scaffold under `frontend/`

## Stack

- FastAPI
- PostgreSQL schema under `migrations/002_v2_schema.sql`
- React + Vite + TypeScript
- Docker-first runtime contract

## Backend Setup

1. Install Python dependencies:

```bash
python3 -m pip install -e .
```

2. Provide a PostgreSQL `DATABASE_URL` and apply V2 migrations.

3. Start the API:

```bash
python3 scripts/run_api.py
```

4. Open the V2 entry:

```text
http://127.0.0.1:8888/
```

## Frontend Setup

1. Install frontend dependencies:

```bash
cd frontend
npm install
```

2. Build the SPA:

```bash
npm run build
```

The FastAPI app serves `frontend/dist` when it exists. If the SPA has not been built yet, `/` falls back to a simple HTML notice and `/docs` remains available for API testing.

## 常用脚本

- `./scripts/v2/bootstrap_backend.sh`：初始化 `.venv` 并安装后端依赖
- `./scripts/v2/apply_v2_migration.sh`：执行 V2 PostgreSQL migration
- `./scripts/v2/run_v2_api.sh`：启动 V2 API
- `./scripts/v2/install_frontend.sh`：安装前端依赖
- `./scripts/v2/build_frontend.sh`：构建 SPA
- `./scripts/v2/compose_up.sh`：启动 Docker Compose 部署
- `./scripts/v2/compose_down.sh`：停止 Docker Compose 部署
- `./scripts/v2/health_check.sh`：检查 API 基础健康状态
- `./scripts/v2/smoke_test.sh`：执行一轮最小 smoke test
- `./scripts/v2/backup_data.sh`：备份 bundle、runtime 目录和 PostgreSQL 数据
- `./scripts/v2/release.sh`：执行备份、启动和健康检查
- `./scripts/v2/rollback.sh`：停止当前 V2 服务，准备回滚
- `./scripts/v2/package_bundle.sh <RUN_ID>`：归档 bundle

也可以直接使用 `Makefile`：

```bash
make bootstrap-backend
make migrate-v2
make build-frontend
make compose-up
make health-check
make smoke-test
```

## 文档导航

- 使用说明：[docs/v2-usage-guide.md](/Users/cgw/ct/self/AI/propagate/docs/v2-usage-guide.md)
- 部署说明：[docs/v2-deployment-guide.md](/Users/cgw/ct/self/AI/propagate/docs/v2-deployment-guide.md)
