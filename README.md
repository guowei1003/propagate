# Propagate

AI 任务执行系统——创建任务，AI 自动规划并执行，支持 Docker 沙箱隔离。

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy + PostgreSQL |
| 前端 | React + Vite + TypeScript |
| 运行时 | Docker 沙箱（`--network none` 隔离） |
| 部署 | Docker Compose |

## 快速开始

### Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone <repo-url>
cd propagate

# 2. 复制环境变量
cp deploy/.env.example .env

# 3. 构建所有镜像
./deploy/scripts/build.sh

# 4. 启动服务（生产模式）
./deploy/scripts/deploy.sh production

# 或开发模式（源码挂载、热重载）
./deploy/scripts/deploy.sh dev
```

访问：
- 前端：`http://localhost`
- API：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

### 本地开发

**后端：**

```bash
cd backend
python3 -m pip install -r requirements.txt

# 确保 PostgreSQL 运行中，DATABASE_URL 环境变量指向它
# 例如：export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/propagate

python3 run.py
# API 运行在 http://localhost:8000
```

**前端：**

```bash
cd frontend
npm install
npm run dev
# 前端运行在 http://localhost:3000
# API 请求代理到 http://localhost:8000
```

## 目录结构

```
propagate/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── main.py       # 应用入口
│   │   ├── config.py     # 配置
│   │   ├── db.py         # 数据库连接
│   │   ├── models.py     # SQLAlchemy 模型
│   │   ├── schemas.py     # Pydantic Schema
│   │   ├── routers/       # API 路由
│   │   │   ├── tasks.py   # 任务 CRUD
│   │   │   ├── profiles.py # 环境配置
│   │   │   └── events.py  # SSE 事件流
│   │   └── services/
│   │       ├── task_service.py  # 业务逻辑
│   │       ├── worker.py   # Docker 执行 Worker
│   │       └── llm.py     # LLM 调用（demo/openai/ollama）
│   ├── Dockerfile         # API 服务镜像
│   └── requirements.txt
├── frontend/              # React 前端
│   ├── src/
│   │   ├── App.tsx        # 根组件 + hash 路由
│   │   ├── components/     # 组件
│   │   ├── lib/api.ts     # API 请求封装
│   │   ├── theme.ts       # 主题系统
│   │   └── presenters.ts  # 数据格式化
│   └── Dockerfile         # Nginx 静态服务镜像
├── deploy/                # 部署配置
│   ├── docker-compose.yml          # 生产
│   ├── docker-compose.dev.yml      # 开发
│   ├── docker/
│   │   ├── api.Dockerfile
│   │   ├── frontend.Dockerfile
│   │   ├── runner.Dockerfile   # 沙箱执行容器
│   │   └── nginx.conf
│   └── scripts/
│       ├── init_db.sh     # 数据库初始化
│       ├── build.sh       # 构建镜像
│       ├── deploy.sh      # 一键部署
│       ├── restart.sh      # 重启服务
│       └── clean.sh        # 清理
└── deploy/.env.example
```

## API 概览

### 任务

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/tasks` | 列出任务（支持 `status` 筛选） |
| `POST` | `/api/tasks` | 创建任务 |
| `GET` | `/api/tasks/{id}` | 获取任务详情 |
| `DELETE` | `/api/tasks/{id}` | 删除任务 |
| `GET` | `/api/tasks/{id}/stream` | SSE 实时事件流 |
| `GET` | `/api/tasks/{id}/events` | 历史事件列表 |

### 环境配置

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/profiles` | 列出配置 |
| `POST` | `/api/profiles` | 创建配置 |
| `GET` | `/api/profiles/{id}` | 获取配置 |
| `PUT` | `/api/profiles/{id}` | 更新配置 |
| `DELETE` | `/api/profiles/{id}` | 删除配置 |

## 配置

`.env` 文件关键变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `postgresql://...` | PostgreSQL 连接字符串 |
| `LLM_PROVIDER` | `demo` | `demo` / `openai` / `ollama` |
| `LLM_API_BASE` | - | OpenAI/Ollama API 地址 |
| `LLM_API_KEY` | - | API Key |
| `LLM_MODEL` | `gpt-4o-mini` | 模型名称 |
| `WORKER_CONCURRENCY` | `3` | 并发执行数 |
| `RUNNER_IMAGE` | `propagate-runner:latest` | Docker 沙箱镜像 |

## LLM 提供商

- **Demo**（默认）：返回基于 prompt 内容生成的模拟响应，无需外部 API
- **OpenAI**：设置 `LLM_PROVIDER=openai` 及相关 API 变量
- **Ollama**：设置 `LLM_PROVIDER=ollama`，`LLM_API_BASE` 指向本地 Ollama 地址

## 部署脚本

```bash
./deploy/scripts/build.sh     # 构建所有 Docker 镜像
./deploy/scripts/deploy.sh   # 部署（production | dev）
./deploy/scripts/restart.sh  # 重启服务（可选指定服务名）
./deploy/scripts/clean.sh    # 清理容器、卷、网络
```
