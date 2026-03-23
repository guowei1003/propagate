from __future__ import annotations

from app.domain.models import DecomposedSubtask, ExecutionPlan


class TaskEvaluatorAgent:
    def _infer_additional_skills(self, subtask: DecomposedSubtask) -> list[str]:
        text = f"{subtask.name} {subtask.description}".lower()
        extras: list[str] = []
        if any(token in text for token in ["api", "接口", "backend", "后端"]):
            extras.append("api_contract")
        if any(token in text for token in ["ui", "页面", "web", "app", "前端"]):
            extras.append("design_system")
        if any(token in text for token in ["test", "测试", "验证"]):
            extras.append("test_automation")
        if any(token in text for token in ["deploy", "发布", "docker", "上线"]):
            extras.append("deployment_pipeline")
        return extras

    def _dedupe(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

    def run(self, subtask: DecomposedSubtask, env_profile: dict, task_id: str, sequence_no: int) -> ExecutionPlan:
        mapping = {
            "backend": ("backend_executor", ["read_repo", "edit_file", "run_command"]),
            "ui": ("frontend_executor", ["read_repo", "edit_file"]),
            "config": ("config_executor", ["edit_file"]),
            "documentation": ("doc_executor", ["generate_report"]),
        }
        template, base_skills = mapping.get(subtask.category, ("generic_executor", ["read_repo"]))
        skills = self._dedupe(base_skills + self._infer_additional_skills(subtask))
        auto_sub_agents = bool(int(env_profile.get("enable_auto_sub_agents") or 0))
        runtime_template = (
            f"tmp_{template}_{task_id.replace('-', '')[:8]}_{sequence_no + 1}"
            if auto_sub_agents
            else template
        )
        return ExecutionPlan(
            agent_template=runtime_template,
            skills=skills,
            timeout_sec=int(env_profile.get("default_timeout_sec") or 300),
            max_retries=int(env_profile.get("max_retries") or 2),
        )


task_evaluator_agent = TaskEvaluatorAgent()
