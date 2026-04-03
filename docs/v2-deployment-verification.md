# Propagate V2 部署验证记录

## 1. 验证目标

本文件用于记录 Propagate V2 的真实部署验证情况，区分：

- 已在当前环境完成验证的步骤
- 因环境限制暂未完成的步骤

## 2. 当前环境

- 工作目录：`/Users/cgw/ct/self/AI/propagate`
- Python 虚拟环境：`.venv`
- 当前日期：`2026-04-02`
- 当前限制：
  - 本机未确认可用的 Docker 运行环境
  - 前端依赖安装曾受到 npm registry 配置影响
  - PostgreSQL 实际联调未在本轮会话内完成

## 3. 已完成验证

### 3.0 代码层验证边界

当前已经完成的是“代码层与脚本层验证”，包括：

- 后端单元测试
- Python 编译检查
- Shell 脚本语法检查
- 健康检查入口测试

尚未完成的是“真实环境联调验证”，即：

- Docker Compose 启动
- PostgreSQL migration
- 真实容器执行
- smoke test 真实跑通

### 3.1 后端单元测试

执行命令：

```bash
.venv/bin/python -m unittest discover -s tests/v2 -v
```

结果：

- 共 28 个测试
- 全部通过

### 3.2 Python 编译检查

执行命令：

```bash
.venv/bin/python -m compileall app/v2 scripts/run_api.py
```

结果：

- V2 Python 模块可编译
- 启动脚本可编译

### 3.3 脚本语法检查

执行命令：

```bash
for f in scripts/v2/*.sh; do bash -n "$f" || exit 1; done
```

结果：

- 所有 `scripts/v2/*.sh` 语法检查通过

### 3.4 应用入口健康检查测试

测试文件：

- `tests/v2/test_app_entry.py`

验证内容：

- `/` 返回 V2 入口页面
- `/healthz` 返回 `{"status": "ok"}`

### 3.5 状态机与主链路辅助测试

当前额外覆盖了：

- 能力自动生成基础逻辑
- 依赖阻塞传播
- env profile 编辑语义
- run 终态/phase 一致性
- guardrails / review / test helper

## 4. 尚未完成的真实部署验证

以下步骤需要具备可用的 Docker 和 PostgreSQL 环境后再执行：

1. `./scripts/v2/compose_up.sh`
2. `./scripts/v2/health_check.sh`
3. `./scripts/v2/smoke_test.sh`
4. `POST /v2/runs/{id}/resume` 触发真实容器执行
5. `POST /v2/runs/{id}/bundle/build` 产出真实 bundle 并下载

## 5. 待验证清单

- [ ] Docker Compose 启动成功
- [ ] PostgreSQL migration 成功执行
- [ ] `health_check.sh` 返回成功
- [ ] `smoke_test.sh` 跑通 profile -> task -> approve -> resume -> bundle
- [ ] bundle 下载接口返回可用归档文件
- [ ] 前端构建并由 `frontend` 容器正确提供

## 6. 建议下一步验证顺序

1. 确认 `docker` 和 `docker compose` 可用
2. 执行 `./scripts/v2/compose_up.sh`
3. 执行 `./scripts/v2/health_check.sh`
4. 执行 `./scripts/v2/smoke_test.sh`
5. 将命令输出、失败日志或成功结果补充到本文件
