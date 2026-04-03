# Propagate V2 部署说明

## 1. 文档目标

本文档描述 Propagate V2 的部署方式，重点覆盖：

- 容器化部署结构
- 启动顺序
- 数据持久化
- 配置项说明
- 发布与回滚建议
- `scripts/v2` 运维脚本说明与推荐执行顺序

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

生产环境推荐把上述变量写入 **`/data/propagate/config/.env`**（由 `ensure_propagate_data_root.sh` 在首次启动时从仓库内 `.env.example` 复制，仅当该文件尚不存在时创建）。`compose_up.sh` / `compose_down.sh` 等会在该文件存在时自动附加 `docker compose --env-file`。仓库根目录的 `.env` 仍可作为本地开发时的默认来源。

### 3.3 数据根目录与权限

默认数据根目录为 **`/data/propagate`**（可通过环境变量 **`PROPAGATE_DATA_ROOT`** 指向其他绝对路径，例如本机无 root 权限时设为 `$HOME/propagate-data`）。其下目录约定见 [第 6 节](#6-数据与产物持久化)。确保运行 Docker 与脚本的用户对 `PROPAGATE_DATA_ROOT` 有读写权限；无法在宿主机创建 `/data/propagate` 时需 `sudo` 建目录并委派权限，或改用自定义 `PROPAGATE_DATA_ROOT`。

## 4. 启动步骤

### 4.1 启动服务

```bash
./scripts/v2/compose_up.sh
```

`compose_up.sh` 会**先**执行 `./scripts/v2/ensure_propagate_data_root.sh`：在数据根下创建缺失子目录（已存在则跳过）；若 **`${PROPAGATE_DATA_ROOT:-/data/propagate}/config/.env`** 不存在且仓库内有 `.env.example`，则复制生成一份供编辑，**不会覆盖已有配置**。然后再启动 Compose。

不推荐完全绕过脚本；若必须手写 `docker compose`，请至少先执行 `ensure_propagate_data_root.sh`，并导出与 Compose 卷路径一致的 **`PROPAGATE_DATA_ROOT`**，且在存在 `/data/propagate/config/.env` 时自行加上 `--env-file`：

```bash
export PROPAGATE_DATA_ROOT="${PROPAGATE_DATA_ROOT:-/data/propagate}"
./scripts/v2/ensure_propagate_data_root.sh
docker compose -f docker-compose.v2.yml --env-file "${PROPAGATE_DATA_ROOT}/config/.env" up --build -d
```

（若尚未创建 `config/.env`，可去掉 `--env-file` 一行，改用仓库根目录 `.env` 供 Compose 插值。）

默认暴露端口：

- `8080`：前端入口
- `8888`：API 服务
- `5432`：PostgreSQL

### 4.2 执行迁移

`docker-compose.v2.yml` 中的 `migrate` 服务会在 `postgres` 健康后、**`api` 启动前**自动执行 `./scripts/v2/apply_v2_migration.sh`（容器内已配置 `DATABASE_URL`）。因此通过 **`compose_up.sh` / `docker compose up` 第一次起栈时，迁移通常不必在宿主机再跑一遍**。

以下情况仍可在**宿主机**手动执行同一脚本（需已安装项目依赖且能连上数据库，见 [第 9 节](#9-运维脚本-scriptsv2)）：

- CI/CD 在「拉起 API 容器之前」单独对目标库执行迁移；
- 调试迁移、或使用非 Compose 的数据库连接串。

```bash
export DATABASE_URL="postgresql://用户:密码@主机:5432/propagate"
./scripts/v2/apply_v2_migration.sh
```

建议在自动化流水线里把迁移放在 API 切流之前，并与当前环境使用的 `DATABASE_URL` 一致。

## 5. 验证步骤

上线后至少检查以下内容：

1. `http://127.0.0.1:8080/` 能打开 SPA。
2. `http://127.0.0.1:8888/docs` 能打开 API 文档。
3. `GET /v2/env-profiles` 返回 200。
4. 创建 demo profile 并调用 `/validate` 成功。
5. 创建一个测试任务，能进入 `WAITING_APPROVAL` 或 `WAITING_USER_INPUT`。
6. 审批后调用 `/v2/runs/{id}/resume`，能生成事件、证据和报告。
7. 调用 `/v2/runs/{id}/bundle/build`，能生成 `manifest.json`。

也可以直接执行（推荐顺序：先快速探活，再业务冒烟）：

```bash
./scripts/v2/health_check.sh
./scripts/v2/smoke_test.sh
```

说明：`health_check.sh` 仅检查 `GET /healthz` 与 `GET /openapi.json`；`smoke_test.sh` 会创建 profile、建任务、审批能力、`resume`、等待终态并调用 `bundle/build`，覆盖面更接近上文 1～7 步，但**不单独调用** `POST /v2/env-profiles/{id}/validate`，若需严格对齐第 4 步请额外用手动或自建步骤调用该接口。

环境变量：

- `API_BASE_URL`：默认 `http://127.0.0.1:8888`，远程或反代时请覆盖。
- `SMOKE_TIMEOUT_SEC`：仅影响 `smoke_test.sh` 轮询超时，默认 `30`。

验证结果请记录到：

- [docs/v2-deployment-verification.md](v2-deployment-verification.md)

## 6. 数据与产物持久化

默认宿主机根目录为 **`PROPAGATE_DATA_ROOT`**（未设置时为 `/data/propagate`）。子目录由 `ensure_propagate_data_root.sh` 确保存在。

### 6.1 PostgreSQL 数据

`postgres` 使用**绑定挂载**（非命名卷）：

```text
${PROPAGATE_DATA_ROOT:-/data/propagate}/postgres -> 容器 /var/lib/postgresql/data
```

### 6.2 应用产物目录

API 容器挂载：

```text
${PROPAGATE_DATA_ROOT:-/data/propagate}/app-data -> 容器 /app/data
```

其中包含：

- `app-data/runtime-v2/`：子任务工作区
- `app-data/bundles/`：bundle 输出

备份脚本将副本写入 **`${PROPAGATE_DATA_ROOT:-/data/propagate}/backups/<时间戳>/`**。若要做灾难恢复，请同时保留 PostgreSQL 数据目录与 `app-data`。

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
${PROPAGATE_DATA_ROOT:-/data/propagate}/app-data/bundles/<RUN_ID>.tar.gz
```

这个文件适合作为交付附件、问题复盘材料或审计留档。

## 9. 运维脚本（scripts/v2）

以下脚本均假定在**仓库根目录**执行（脚本内部会 `cd` 到根目录）。持久化路径默认以 **`PROPAGATE_DATA_ROOT`**（默认 `/data/propagate`）为准，与 `docker-compose.v2.yml` 中卷定义一致；本机开发可 `export PROPAGATE_DATA_ROOT=$HOME/propagate-data` 等。`compose_helpers.sh` 供脚本内部 source，勿单独当作入口执行。

### 9.1 脚本一览

| 脚本 | 作用 |
|------|------|
| `ensure_propagate_data_root.sh` | 确保 `PROPAGATE_DATA_ROOT` 下 `postgres`、`app-data`、`config`、`backups` 目录存在；仅在 `config/.env` 缺失且仓库有 `.env.example` 时复制生成，不覆盖已有文件。 |
| `compose_up.sh` | 先执行 `ensure_propagate_data_root.sh`，再 `docker compose … up --build -d` 与 `ps`；若存在 `config/.env` 则自动 `--env-file`。 |
| `compose_down.sh` | 与数据根、`config/.env` 约定一致的 `docker compose down`。 |
| `apply_v2_migration.sh` | 对 `DATABASE_URL` 执行 `migrations/002_v2_schema.sql`（需 `psycopg`）。Compose 内 `migrate` 服务已调用；宿主机跑时需先 `export DATABASE_URL`。 |
| `health_check.sh` | 请求 `API_BASE_URL` 的 `/healthz` 与 `/openapi.json`，用于极简探活。 |
| `smoke_test.sh` | 端到端冒烟：建 env profile、建任务、按能力审批、`resume`、轮询终态、`bundle/build`。依赖 `API_BASE_URL`（及可选 `SMOKE_TIMEOUT_SEC`）。 |
| `backup_data.sh` | 将 `app-data/bundles`、`app-data/runtime-v2` 复制到 `${PROPAGATE_DATA_ROOT}/backups/<时间戳>/`；若本机存在 `docker` 且 Compose 栈可 `exec postgres`，则额外 `pg_dump` 到同目录的 `propagate.sql`。 |
| `release.sh` | **顺序**：`backup_data.sh` → `compose_up.sh` → `health_check.sh`；**不**自动运行 `smoke_test.sh`，发布后建议手动再跑。 |
| `rollback.sh` | 等价于 `compose_down.sh`（整栈停止）；切回旧镜像、保库、导出 bundle 等需按 [7.2 回滚建议](#72-回滚建议) 人工处理。 |
| `package_bundle.sh` | 将 `app-data/bundles/<RUN_ID>/` 打成 `app-data/bundles/<RUN_ID>.tar.gz`。参数：`RUN_ID`。 |
| `bootstrap_backend.sh` | **本地开发**：创建/使用 `.venv` 并 `pip install -e .`。 |
| `run_v2_api.sh` | **本地开发**：用 `.venv` 启动 `scripts/run_api.py`（非 Docker）。 |
| `install_frontend.sh` | **本地前端**：在 `frontend/` 下 `npm install`（可用 `NPM_REGISTRY` 指定 registry）。 |
| `build_frontend.sh` | **本地前端**：必要时先安装依赖，再 `npm run build`，产出 `frontend/dist`。 |

### 9.1.1 默认国内源与镜像优化

- `Dockerfile.api` 默认将 Debian `apt` 源切到阿里云镜像，并使用阿里云 PyPI 镜像安装 Python 依赖。
- `Dockerfile.frontend` 与本地前端脚本默认使用 `https://registry.npmmirror.com`。
- V2 Compose 中的 `api` / `migrate` 容器只安装 Docker CLI，不安装完整 Docker Engine；运行时通过宿主机挂载的 `/var/run/docker.sock` 与宿主机 Docker 通信。
- 如需覆盖默认值，可在 `${PROPAGATE_DATA_ROOT}/config/.env` 中设置 `APT_MIRROR`、`PIP_INDEX_URL`、`NPM_REGISTRY`。

### 9.2 推荐执行顺序（按场景）

**场景 A：首次部署（Docker Compose，单机）**

1. 准备 Docker、Compose；确保对 `PROPAGATE_DATA_ROOT`（默认 `/data/propagate`）有写权限。配置可放在 `config/.env`（推荐）或仓库根 `.env`。
2. `./scripts/v2/compose_up.sh`（内部先 `ensure_propagate_data_root.sh`，再起 `postgres` → `migrate` → `api` → `frontend`）。
3. `./scripts/v2/health_check.sh`（若 API 不在本机，设置 `API_BASE_URL`）。
4. `./scripts/v2/smoke_test.sh`（建议；生产可仅在预发执行）。

**场景 B：仅宿主机执行迁移（如 CI、无外网 Compose）**

1. 安装与仓库一致的 Python 依赖（含 `psycopg[binary]`）。
2. `export DATABASE_URL=...`（目标 PostgreSQL，网络可达）。
3. `./scripts/v2/apply_v2_migration.sh`。

**场景 C：发版（使用仓库提供的 `release.sh`）**

1. `./scripts/v2/release.sh`（备份 → 起栈 → 健康检查）。
2. `./scripts/v2/smoke_test.sh`（脚本内未包含，需单独执行）。
3. 若你们流水线包含「构建并推送镜像」，应在 `release.sh` 之前完成镜像更新与策略切换；`release.sh` 本身不构建、不推送镜像。

**场景 D：例行备份**

1. 保持 `postgres` 与 Stack 可访问（`pg_dump` 依赖 `docker compose exec postgres`）。
2. `./scripts/v2/backup_data.sh`。
3. 将 `${PROPAGATE_DATA_ROOT}/backups/<时间戳>/` 与既定备份策略（拷贝、对象存储等）对齐。

**场景 E：停机 / 紧急止损**

1. `./scripts/v2/rollback.sh` 或 `./scripts/v2/compose_down.sh`。
2. 按 [7.2 回滚建议](#72-回滚建议) 恢复入口与镜像版本。

**场景 F：Run 归档**

1. 在任务结束后：`./scripts/v2/package_bundle.sh <RUN_ID>`（与 [第 8 节](#8-打包与归档) 一致）。

**场景 G：本地开发（不使用 Docker 跑 API）**

1. `./scripts/v2/bootstrap_backend.sh`
2. `./scripts/v2/run_v2_api.sh`
3. 改前端时：`./scripts/v2/install_frontend.sh`（按需）、`./scripts/v2/build_frontend.sh`

### 9.3 与 Compose 服务顺序的关系

Compose 依赖链概括为：`postgres`（健康）→ `migrate`（一次性成功）→ `api`（健康）→ `frontend`。与脚本对应关系：`compose_up.sh` 触发上述全部；`apply_v2_migration.sh` 在 `migrate` 容器中已执行一次，宿主机重复执行前请确认 SQL 幂等性或运维规范是否允许。

## 10. 已知限制

- 若你曾使用旧版 Compose 的 **`propagate-postgres` 命名卷** 部署，切换到 **`/data/propagate/postgres` 绑定挂载** 后，需要将原卷中的数据迁移至新目录（或继续使用命名卷需自行改回 compose，与本仓库默认配置不一致）。
- 当前代码已经实现了 Docker 执行契约，但实际执行仍依赖宿主机安装 Docker。
- 前端构建依赖 npm registry，如果宿主机配置了不可达的私有源，需要显式覆盖 registry。
- `DATABASE_URL` 迁移脚本依赖 `psycopg[binary]`。
- 首版没有登录系统，审批人由接口请求直接传入。
