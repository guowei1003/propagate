# Propagate Agent Harness

Propagate 现在是一个面向代码/API 自动化任务的 agent harness。它不是单次 prompt 执行器，而是把任务放进一条完整、可监督的执行链：

1. 用户提交任务目标、约束与交付物
2. `intake` 生成结构化 mission
3. 系统自动选配所需 agents
4. `planner` 编译强类型执行计划
5. `supervisor` 监督步骤执行、重试、replan 与预算
6. `verifier` 根据成功标准输出验证结果
7. 控制台展示 mission、plan、timeline、approval 和 artifacts

## 目录

```text
apps/api    FastAPI 控制面、运行时、工具与服务层
apps/web    React 监督台
agents      内置 agent registry
deploy      Docker Compose 与 Dockerfiles
evals       golden task 场景
docs        架构与评估说明
```

## 本地开发

### API

```bash
uv sync
PYTHONPATH=apps/api .venv/bin/uvicorn app.main:app --reload
```

### Web

```bash
cd apps/web
npm install
npm run dev
```

## Docker

生产态：

```bash
cd deploy
docker compose up --build
```

或者直接在服务器根目录执行：

```bash
bash ./dev.sh
```

开发态：

```bash
cd deploy
docker compose -f docker-compose.dev.yml up --build
```

## 服务器一键部署

默认会自动使用并创建这些目录：

```bash
/data/propagate/config
/data/propagate/postgres
/data/propagate/app
```

执行：

```bash
bash ./dev.sh
```

脚本会自动完成这些动作：

1. 创建 `/data/propagate/...` 目录
2. 自动生成 `/data/propagate/config/propagate.env`（首次执行）
3. 自动 build 最新镜像
4. 自动执行当前服务器上的 `docker compose up -d`
5. 自动把数据库目录和应用数据目录挂载进容器

如果你要改目录，可以传参：

```bash
bash ./dev.sh --base-dir /data/my-propagate
```

如果你要指定自己的配置文件：

```bash
bash ./dev.sh --env-file /data/my-propagate/config/prod.env
```

## 服务器打包脚本

如果你想在服务器上直接执行“编译 + 打包 + 输出到指定目录”，可以使用：

```bash
bash deploy/scripts/build_release.sh --output-dir /path/to/output
```

如果希望打包前顺便跑后端和前端测试：

```bash
bash deploy/scripts/build_release.sh --output-dir /path/to/output --with-tests
```

脚本会输出两份产物：

1. 解包后的发布目录
2. 对应的 `.tar.gz` 压缩包

## 当前边界

- v1 是单租户、本地优先控制面
- 默认提供 mock provider，真实 OpenAI provider 需要配置 `PROPAGATE_OPENAI_API_KEY`
- Docker runner 已落代码和镜像文件，但当前工作机没有可用的 `docker` 命令，真实沙箱执行需要在具备 Docker 的环境验证
