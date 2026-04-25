# Propagate Agent Harness

面向「可约束、可编排、可监督、可恢复、可评估」的多智能体运行底座：Python（FastAPI + LangGraph）控制面、PostgreSQL 持久化、Docker 沙箱执行、React 监督台。

## Python 虚拟环境（推荐）

本仓库要求 **Python 3.12 或 3.13**（勿用 3.14，部分依赖尚未完全支持）。任选其一：

**方式 A：`python -m venv`（需本机已安装 3.12/3.13）**

```bash
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e ".[dev]"
```

**方式 B：用 uv 安装固定 Python 再建 venv**

```bash
uv python install 3.12
uv venv --python 3.12 .venv
source .venv/bin/activate
pip install -e ".[dev]"
# 或: uv sync（使用 uv 锁文件时）
```

启动 API 前请先 `source .venv/bin/activate`，或在命令中使用 `.venv/bin/python` / `.venv/bin/uvicorn`。

## 快速开始

```bash
# Python API（本地 SQLite 默认）
source .venv/bin/activate
cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd apps/web && npm install && npm run dev
```

## Docker Compose（PostgreSQL + API + Web + Runner 镜像）

```bash
docker compose -f deploy/docker-compose.yml up --build
```

- API: `http://localhost:8000`（文档 `/docs`）
- Web: `http://localhost:5173`（开发）或经 Compose 映射的端口

## 环境变量（前缀 `PROPAGATE_`）

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | 默认 SQLite；生产使用 `postgresql+asyncpg://...` |
| `CHECKPOINT_DATABASE_URL` | LangGraph checkpoint；Postgres 时用 `postgresql://...` |
| `OPENAI_API_KEY` | OpenAI 时使用 |
| `DEFAULT_PROVIDER` | `mock`（测试/CI）或 `openai` |
| `RUNNER_IMAGE` | 沙箱镜像（见 `deploy/docker/runner.Dockerfile`） |

## 文档

- [架构说明](docs/architecture/agent-harness.md)
- [Golden tasks 评估](docs/evals/golden-tasks.md)

## 风险边界（v1）

- 单租户、无 RBAC；默认沙箱 `--network none`，外网 HTTP 仅经 Profile 白名单工具。
- 不做浏览器自动化、不做跨任务长期记忆。

## 测试

```bash
uv run pytest apps/api/tests -q
cd apps/web && npm test
```
