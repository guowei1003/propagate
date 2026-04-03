# Propagate V2 部署说明

## 1. 文档目标

本文档描述 Propagate V2 的部署方式，重点覆盖：

- 容器化部署结构
- 启动顺序
- 数据持久化
- 配置项说明
- 发布与回滚建议

## 2. 部署架构

V2 当前采用单机 Docker Compose 方案，包含 3 个服务：

- `postgres`：主数据库
- `api`：FastAPI 应用
- `frontend`：Nginx 托管 SPA，并反向代理 `/v2`、`/docs`、`/openapi.json`

对应文件：

- `docker-compose.v2.yml`
- `Dockerfile.api`
- `Dockerfile.frontend`
- `deploy/nginx/frontend.conf`

## 3. 部署前准备

### 3.1 必备条件

- Docker 24 或以上
- Docker Compose v2
- 可访问的模型服务（如果不是 `demo` 模式）

### 3.2 环境变量

部署前建议在宿主机准备 `.env` 文件，至少包括：

```bash
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/propagate
LLM_PROVIDER_TYPE=openai_compatible
LLM_API_BASE_URL=https://your-provider.example/v1
LLM_API_KEY=your-api-key
LLM_DEFAULT_MODEL=gpt-4o-mini
LLM_REVIEW_MODEL=gpt-4o
LLM_TEST_MODEL=gpt-4o-mini
LLM_CAPABILITY_GENERATION_MODEL=gpt-4o-mini
LLM_REPORT_MODEL=gpt-4o-mini
```

如果只做联调，可用：

```bash
LLM_PROVIDER_TYPE=demo
```

## 4. 启动步骤

### 4.1 启动服务

```bash
./scripts/v2/compose_up.sh
```

等价命令：

```bash
docker compose -f docker-compose.v2.yml up --build -d
```

默认暴露端口：

- `8080`：前端入口
- `8000`：API 服务
- `5432`：PostgreSQL

### 4.2 执行迁移

容器启动后仍需执行数据库迁移，可在宿主机设置同样的 `DATABASE_URL` 后运行：

```bash
./scripts/v2/apply_v2_migration.sh
```

建议把迁移加入你的 CI/CD 流程，在 API 切流前先执行。

## 5. 验证步骤

上线后至少检查以下内容：

1. `http://127.0.0.1:8080/` 能打开 SPA。
2. `http://127.0.0.1:8000/docs` 能打开 API 文档。
3. `GET /v2/env-profiles` 返回 200。
4. 创建 demo profile 并调用 `/validate` 成功。
5. 创建一个测试任务，能进入 `WAITING_APPROVAL` 或 `WAITING_USER_INPUT`。
6. 审批后调用 `/v2/runs/{id}/resume`，能生成事件、证据和报告。
7. 调用 `/v2/runs/{id}/bundle/build`，能生成 `manifest.json`。

也可以直接执行：

```bash
./scripts/v2/health_check.sh
./scripts/v2/smoke_test.sh
```

验证结果请记录到：

- [docs/v2-deployment-verification.md](/Users/cgw/ct/self/AI/propagate/docs/v2-deployment-verification.md)

## 6. 数据与产物持久化

### 6.1 PostgreSQL 数据

`postgres` 服务使用 Docker volume：

```text
propagate-postgres
```

### 6.2 本地产物目录

API 容器挂载：

```text
./data -> /app/data
```

其中包含：

- `data/runtime-v2/`：子任务工作区
- `data/bundles/`：bundle 输出

如果要做备份，建议同时备份 PostgreSQL 和 `data/` 目录。

## 7. 发布建议

### 7.1 推荐发布顺序

1. 构建并推送新镜像。
2. 启动 PostgreSQL。
3. 执行 V2 migration。
4. 启动 API。
5. 启动 frontend。
6. 跑一轮 smoke test。
7. 对外切流。

### 7.2 回滚建议

如果新版本异常，优先按以下顺序回滚：

1. 停掉 frontend，避免继续暴露不稳定入口。
2. 切回旧 API 或旧镜像。
3. 保留 PostgreSQL 数据，不要直接清库。
4. 导出异常 run 的 bundle 与日志，用于复盘。

## 8. 打包与归档

单个 run 完成后，建议执行：

```bash
./scripts/v2/package_bundle.sh <RUN_ID>
```

产出归档文件：

```text
data/bundles/<RUN_ID>.tar.gz
```

这个文件适合作为交付附件、问题复盘材料或审计留档。

## 9. 已知限制

- 当前代码已经实现了 Docker 执行契约，但实际执行仍依赖宿主机安装 Docker。
- 前端构建依赖 npm registry，如果宿主机配置了不可达的私有源，需要显式覆盖 registry。
- `DATABASE_URL` 迁移脚本依赖 `psycopg[binary]`。
- 首版没有登录系统，审批人由接口请求直接传入。
