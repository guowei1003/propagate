from __future__ import annotations

from app.domain.models import DecomposedSubtask
from app.services.llm_service import llm_service


class TaskDecomposerAgent:
    def run(self, task: dict, requirement: dict, env_profile: dict | None = None) -> list[DecomposedSubtask]:
        llm_hint = llm_service.generate_json(
            f"Decompose task into backend, ui, config, or documentation work.\nTask: {task['title']}\nPrompt: {task['prompt']}",
            "task_decomposition",
            env_profile,
            purpose="default",
        )
        prompt = f"{task['title']} {task['prompt']} {requirement['scope']}".lower()
        items: list[DecomposedSubtask] = []

        backend_needed = any(token in prompt for token in ["api", "后端", "agent", "system", "服务"])
        ui_needed = any(token in prompt for token in ["ui", "页面", "前端", "dashboard", "view"])
        config_needed = any(token in prompt for token in ["配置", "model", "timeout", "环境"])

        if not backend_needed and not ui_needed and not config_needed:
            backend_needed = True

        if backend_needed:
            items.append(
                DecomposedSubtask(
                    name="实现后端编排流程",
                    description="实现任务解析、子任务拆解、执行闭环以及日志记录。",
                    category="backend",
                    priority=10,
                    depends_on=[],
                    acceptance={
                        "focus": ["task orchestration", "state management", "events"],
                        "model": llm_hint["model"],
                    },
                )
            )
        if ui_needed:
            depends = [0] if backend_needed else []
            items.append(
                DecomposedSubtask(
                    name="实现任务管理 UI",
                    description="实现任务列表、详情、澄清输入、日志查看和报告展示。",
                    category="ui",
                    priority=20,
                    depends_on=depends,
                    acceptance={"focus": ["task list", "task detail", "logs", "report"], "model": llm_hint["model"]},
                )
            )
        if config_needed:
            depends = [0] if backend_needed else []
            items.append(
                DecomposedSubtask(
                    name="实现环境配置能力",
                    description="实现模型、超时、并发和最大重试次数配置。",
                    category="config",
                    priority=30,
                    depends_on=depends,
                    acceptance={
                        "focus": ["model config", "timeout config", "concurrency config"],
                        "model": llm_hint["model"],
                    },
                )
            )

        if len(items) == 1:
            items.append(
                DecomposedSubtask(
                    name="整理交付结果与说明",
                    description="补充交付说明、验证路径和最终交付摘要。",
                    category="documentation",
                    priority=40,
                    depends_on=[0],
                    acceptance={"focus": ["delivery summary", "verification notes"], "model": llm_hint["model"]},
                )
            )
        return items


task_decomposer_agent = TaskDecomposerAgent()
