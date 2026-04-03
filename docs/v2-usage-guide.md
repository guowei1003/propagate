# Propagate V2 使用说明

## 1. 文档目标

本文档说明 Propagate V2 的本地使用方式，覆盖以下内容：

- 环境准备
- 后端启动
- 前端启动与构建
- 环境配置创建
- 任务创建与审批执行
- bundle 构建与打包

## 2. 环境准备

### 2.1 基础依赖

建议准备以下环境：

- Python 3.11 或以上
- Node.js 22 或以上
- PostgreSQL 16 或以上
- Docker（用于真实执行与容器化部署）

### 2.2 环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

重点变量如下：

- `DATABASE_URL`：V2 使用的 PostgreSQL 连接串
- `LLM_PROVIDER_TYPE`：`demo` 或 `openai_compatible`
- `LLM_API_BASE_URL`：OpenAI 兼容接口地址
- `LLM_API_KEY`：模型服务密钥
- `LLM_DEFAULT_MODEL`：默认模型
- `LLM_REVIEW_MODEL`：Review 阶段模型
- `LLM_TEST_MODEL`：Test 阶段模型
- `LLM_CAPABILITY_GENERATION_MODEL`：能力生成模型
- `LLM_REPORT_MODEL`：报告生成模型

## 3. 本地启动

### 3.1 安装后端依赖

```bash
./scripts/v2/bootstrap_backend.sh
```

### 3.2 执行 V2 数据库迁移

```bash
export DATABASE_URL='postgresql://postgres:postgres@127.0.0.1:5432/propagate'
./scripts/v2/apply_v2_migration.sh
```

### 3.3 安装与构建前端

如果默认 npm registry 不可用，可覆盖为官方源：

```bash
export NPM_REGISTRY='https://registry.npmjs.org/'
./scripts/v2/install_frontend.sh
./scripts/v2/build_frontend.sh
```

### 3.4 启动 API

```bash
./scripts/v2/run_v2_api.sh
```

启动后访问：

- 前端入口：`http://127.0.0.1:8000/`
- API 文档：`http://127.0.0.1:8000/docs`

如果 `frontend/dist` 尚未构建，根路径会返回一个 V2 占位页面，并提示使用 `/docs` 调试 API。

## 4. 业务使用流程

### 4.1 创建环境配置

使用 `POST /v2/env-profiles` 创建环境配置。建议至少填写以下字段：

- `name`
- `provider_type`
- `api_base_url`
- `api_key`
- `default_model`
- `review_model`
- `test_model`
- `capability_generation_model`
- `report_model`

创建后可调用 `POST /v2/env-profiles/{id}/validate` 验证连通性与模型选择结果。

### 4.2 创建任务

调用 `POST /v2/tasks`：

```json
{
  "title": "实现 V2 任务编排",
  "prompt": "实现任务工作台、能力审批和 bundle 下载",
  "env_profile_id": "your-profile-id",
  "model_overrides": {
    "review": "gpt-4o"
  }
}
```

系统会执行以下动作：

1. 创建任务和 run。
2. 执行需求分析。
3. 如有缺失信息，生成澄清问题。
4. 如信息充分，生成子任务与候选能力。
5. 将 run 状态置为 `WAITING_APPROVAL`。

### 4.3 回答澄清

如果任务进入 `WAITING_USER_INPUT`，调用：

`POST /v2/tasks/{task_id}/clarifications/{round_id}/answer`

提交后系统会重新分析需求，并继续生成子任务与候选能力。

### 4.4 审批能力

调用以下接口完成审批：

- `POST /v2/capabilities/{id}/approve`
- `POST /v2/capabilities/{id}/reject`

首版执行前门禁要求：子任务绑定到的 agent 和 skill 均必须是 `approved`。

### 4.5 恢复执行

所有必需能力审批完成后，调用：

`POST /v2/runs/{run_id}/resume`

系统会：

1. 准备子任务工作区。
2. 物化执行 manifest。
3. 尝试以 Docker 命令执行。
4. 采集 stdout、stderr、退出码和输出文件。
5. 写入执行证据、事件和报告。

## 5. bundle 构建与打包

### 5.1 构建 bundle

调用：

`POST /v2/runs/{run_id}/bundle/build`

默认输出目录：

```text
data/bundles/{run_id}/
```

目录结构如下：

```text
product/
agents/
skills/
logs/
reports/
manifest.json
```

### 5.2 打包 bundle

```bash
./scripts/v2/package_bundle.sh <RUN_ID>
```

默认输出：

```text
data/bundles/<RUN_ID>.tar.gz
```

## 6. 常见问题

### 6.1 PostgreSQL 驱动未安装

如果运行迁移时报 `No module named 'psycopg'`，先执行：

```bash
.venv/bin/pip install --index-url https://pypi.org/simple 'psycopg[binary]'
```

### 6.2 npm registry 不可达

如果当前环境被自定义 registry 卡住，可显式覆盖：

```bash
NPM_REGISTRY='https://registry.npmjs.org/' ./scripts/v2/install_frontend.sh
```

### 6.3 Docker 不可用

若本机未安装 Docker，`resume` 执行会退化为记录失败证据，方便后续人工介入和审计。
