# 后端模块骨架设计

## 1. 目标

本文档用于把总体方案进一步收敛成可开发的后端模块骨架，目标是：

- 明确单体应用下的目录结构。
- 明确每个模块的职责边界。
- 明确任务状态推进由谁负责。
- 明确 Agent 调用、日志写入、任务调度的调用关系。
- 保持低依赖，不引入额外工作流引擎和消息队列。

## 2. 建议目录

```text
app/
  main.py
  config.py
  db.py
  enums.py
  api/
    routes/
      tasks.py
      subtasks.py
      env_profiles.py
      events.py
      pages.py
    schemas/
      tasks.py
      subtasks.py
      env_profiles.py
      events.py
  domain/
    entities/
      task.py
      subtask.py
      agent_run.py
      event.py
    value_objects/
      requirement.py
      execution_plan.py
      review_result.py
      test_result.py
  repositories/
    task_repository.py
    requirement_repository.py
    clarification_repository.py
    subtask_repository.py
    dependency_repository.py
    event_repository.py
    agent_run_repository.py
    report_repository.py
    env_profile_repository.py
  services/
    llm_service.py
    prompt_service.py
    artifact_service.py
    event_service.py
    lock_service.py
    task_query_service.py
  agents/
    base.py
    requirement_analyzer.py
    task_decomposer.py
    task_evaluator.py
    executor.py
    code_review.py
    tester.py
    reporter.py
  orchestrator/
    task_orchestrator.py
    subtask_orchestrator.py
    dependency_resolver.py
    retry_policy.py
  workers/
    scheduler.py
    subtask_worker.py
  web/
    templates/
      base.html
      tasks/
      env_profiles/
    static/
      app.css
      app.js
tests/
  unit/
  integration/
scripts/
  run_api.py
  run_worker.py
```

## 3. 模块职责

### 3.1 `main.py`

职责：

- 创建 FastAPI 应用。
- 挂载路由。
- 初始化配置、数据库连接。
- 注册应用生命周期钩子。

不负责：

- 业务编排。
- Agent 调用。

### 3.2 `config.py`

职责：

- 统一读取环境变量。
- 暴露数据库连接、默认模型、日志级别、工作目录等配置。

建议包含：

- `DATABASE_URL`
- `WORKSPACE_ROOT`
- `DEFAULT_MODEL`
- `DEFAULT_TIMEOUT_SEC`
- `WORKER_POLL_INTERVAL_SEC`
- `MAX_GLOBAL_CONCURRENCY`

### 3.3 `db.py`

职责：

- 提供数据库连接工厂。
- 管理事务上下文。
- 对外暴露轻量查询接口。

建议原则：

- 不在这里写业务 SQL。
- 业务 SQL 放到各自 repository 中。

### 3.4 `api/routes/*`

职责：

- HTTP 入参校验。
- 调用 service 或 orchestrator。
- 返回 API 响应或 HTML 页面。

不负责：

- 复杂业务判断。
- 状态流转。

### 3.5 `repositories/*`

职责：

- 负责单表或少量关联表的读写。
- 屏蔽 SQL 细节。
- 为 orchestrator 和 service 提供稳定数据访问接口。

接口示例：

- `TaskRepository.create(...)`
- `TaskRepository.update_status(...)`
- `SubTaskRepository.fetch_ready_for_update(...)`
- `EventRepository.append(...)`

### 3.6 `services/*`

职责：

- 提供跨模块复用的基础能力。
- 不持有复杂状态机。

建议拆分：

- `llm_service.py`：封装模型调用。
- `prompt_service.py`：管理各 Agent prompt 模板。
- `artifact_service.py`：统一保存报告、日志、代码产物。
- `event_service.py`：统一写事件并决定是否推送 SSE。
- `lock_service.py`：封装数据库锁和抢占逻辑。

### 3.7 `agents/*`

职责：

- 完成某个环节的智能推理。
- 接收结构化输入，输出结构化结果。

关键要求：

- 所有 Agent 输出都要先过 schema 校验。
- 失败不能直接改数据库状态，只返回结果给 orchestrator。

### 3.8 `orchestrator/*`

职责：

- 掌控主任务和子任务状态推进。
- 决定是否进入澄清。
- 决定是否可以分发并行任务。
- 决定何时触发 Review/Test/Retry。

这是系统核心，所有状态变化都应尽量收敛到这里。

### 3.9 `workers/*`

职责：

- 以后台循环方式轮询可执行任务。
- 领取并执行子任务。
- 把执行结果回交给 orchestrator。

建议拆分：

- `scheduler.py`：负责周期性扫描任务。
- `subtask_worker.py`：负责执行具体子任务流程。

## 4. 核心调用关系

### 4.1 创建任务

```text
POST /api/tasks
-> TaskRepository.create
-> EventService.append(task.created)
-> TaskOrchestrator.start_requirement_analysis
```

### 4.2 需求解析

```text
TaskOrchestrator.start_requirement_analysis
-> RequirementAnalyzer.run
-> RequirementRepository.save_version
-> if missing_info:
     ClarificationRepository.create_round
     TaskRepository.update_status(WAITING_USER_INPUT)
     EventService.append(requirement.clarification.requested)
   else:
     TaskRepository.update_phase(TASK_DECOMPOSING)
```

### 4.3 子任务拆解和评估

```text
TaskOrchestrator.decompose
-> TaskDecomposer.run
-> SubTaskRepository.bulk_create
-> DependencyRepository.bulk_create
-> TaskEvaluator.run_each
-> SubTaskRepository.update_execution_plan
-> SubTaskOrchestrator.mark_ready_nodes
```

### 4.4 子任务执行闭环

```text
Worker.poll
-> SubTaskRepository.fetch_ready_for_update
-> SubTaskRepository.mark_running
-> ExecutorAgent.run
-> CodeReviewAgent.run
-> TestAgent.run
-> if review/test passed:
     SubTaskRepository.mark_completed
   else:
     RetryPolicy.decide
     SubTaskOrchestrator.retry_or_escalate
```

### 4.5 最终报告

```text
TaskOrchestrator.on_all_subtasks_finished
-> ReportAgent.run
-> ReportRepository.save
-> TaskRepository.mark_completed
-> EventService.append(task.report.generated)
```

## 5. 关键类建议

### 5.1 `TaskOrchestrator`

建议方法：

- `create_task(...)`
- `start_requirement_analysis(task_id)`
- `submit_clarification_answers(task_id, round_id, answers)`
- `decompose_task(task_id)`
- `evaluate_subtasks(task_id)`
- `refresh_task_progress(task_id)`
- `finalize_task(task_id)`

### 5.2 `SubTaskOrchestrator`

建议方法：

- `mark_ready_nodes(task_id)`
- `start_subtask(sub_task_id, worker_id)`
- `complete_subtask(sub_task_id, output_summary)`
- `handle_review_failure(sub_task_id, review_result)`
- `handle_test_failure(sub_task_id, test_result)`
- `retry_or_escalate(sub_task_id, reason)`

### 5.3 `RetryPolicy`

输入：

- 当前阶段
- 已重试次数
- 最大重试次数
- 失败类型

输出：

- `retry`
- `needs_human_review`
- `fail_task`

### 5.4 `LLMService`

建议方法：

- `generate_structured(prompt, response_schema, model, timeout_sec)`
- `generate_text(prompt, model, timeout_sec)`

要求：

- 统一处理模型调用超时。
- 统一记录 token 和耗时信息。

## 6. API 分层建议

推荐分为两类接口：

### 6.1 机器接口

- `/api/tasks`
- `/api/subtasks`
- `/api/env-profiles`
- `/api/tasks/{task_id}/events`
- `/api/tasks/{task_id}/stream`

特点：

- 返回 JSON。
- 用于自动化对接或 HTMX 异步刷新。

### 6.2 页面接口

- `/tasks`
- `/tasks/{task_id}`
- `/env-profiles`

特点：

- 返回 HTML。
- 使用服务端模板渲染。

## 7. SSE 实时日志设计

SSE 由 `events.py` 提供：

- 订阅地址：`/api/tasks/{task_id}/stream`
- 数据来源：`task_events` 表
- 发送策略：轮询数据库新事件并增量推送

事件格式建议：

```json
{
  "id": 1024,
  "task_id": "uuid",
  "sub_task_id": "uuid",
  "event_type": "subtask.started",
  "level": "info",
  "message": "Subtask started by worker-1",
  "created_at": "2026-03-09T10:00:00Z"
}
```

首版实现建议：

- SSE 连接每 1 秒拉取一次比 `last_event_id` 更大的事件。
- 不做复杂消息代理。

## 8. Worker 设计

### 8.1 `scheduler.py`

职责：

- 周期扫描处于运行中的主任务。
- 调用 `SubTaskOrchestrator.mark_ready_nodes(task_id)`。
- 唤醒子任务执行。

### 8.2 `subtask_worker.py`

职责：

- 抢占 `READY` 子任务。
- 执行 `Executor -> Review -> Test`。
- 记录每一步的 `agent_runs` 和 `task_events`。

### 8.3 抢占 SQL 设计思路

核心逻辑：

```sql
SELECT id
FROM sub_tasks
WHERE status = 'READY'
ORDER BY priority ASC, created_at ASC
FOR UPDATE SKIP LOCKED
LIMIT 1;
```

说明：

- 这个模式足以支撑首版并发执行。
- 不需要额外引入 Redis 队列。

## 9. Agent 实现边界

### 9.1 Requirement Analyzer

只负责：

- 提炼需求。
- 找缺失信息。
- 生成澄清问题。

不负责：

- 直接拆任务。
- 决定执行策略。

### 9.2 Task Decomposer

只负责：

- 产出子任务和依赖关系。

不负责：

- 选择模型。
- 决定重试次数。

### 9.3 Task Evaluator

只负责：

- 为子任务选择模板、Skill、超时和最大重试次数。

不负责：

- 真正执行代码。

### 9.4 Executor

只负责：

- 完成子任务产出。

不负责：

- 直接宣布成功。

### 9.5 Review/Test

只负责：

- 给出通过与否及结构化原因。

不负责：

- 直接改代码。

## 10. 最小可运行骨架顺序

建议按这个顺序建工程：

1. 建 `app/main.py`、`config.py`、`db.py`。
2. 建 `repositories` 和基础表读写。
3. 建 `api/routes/tasks.py` 和页面 `pages.py`。
4. 建 `event_service.py` 和 SSE 接口。
5. 建 `TaskOrchestrator`。
6. 建 `RequirementAnalyzer` 和 `TaskDecomposer`。
7. 建 `workers/subtask_worker.py`。
8. 再接 `Review`、`Test`、`Report`。

## 11. 首批必须编写的测试

优先写这几类：

- 创建任务后状态是否正确。
- 需求不清时是否进入 `WAITING_USER_INPUT`。
- 子任务依赖满足后是否进入 `READY`。
- Review/Test 失败后是否正确进入重试。
- 超过最大重试次数后是否进入 `NEEDS_HUMAN_REVIEW`。
- SSE 是否能按事件 ID 增量返回日志。

## 12. 结论

后端设计应坚持一个原则：所有复杂性收敛到 Orchestrator 和数据库状态，而不是散落在 API、Worker 或 Agent 内部。这样即便后续要引入 Redis、Celery 或 Temporal，也只是替换调度层，而不会推翻核心业务模型。
