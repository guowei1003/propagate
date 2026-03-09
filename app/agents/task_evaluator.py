from __future__ import annotations

from app.domain.models import DecomposedSubtask, ExecutionPlan


class TaskEvaluatorAgent:
    def run(self, subtask: DecomposedSubtask, env_profile: dict) -> ExecutionPlan:
        mapping = {
            "backend": ("backend_executor", ["read_repo", "edit_file", "run_command"]),
            "ui": ("frontend_executor", ["read_repo", "edit_file"]),
            "config": ("config_executor", ["edit_file"]),
            "documentation": ("doc_executor", ["generate_report"]),
        }
        template, skills = mapping.get(subtask.category, ("generic_executor", ["read_repo"]))
        return ExecutionPlan(
            agent_template=template,
            skills=skills,
            timeout_sec=int(env_profile["default_timeout_sec"]),
            max_retries=int(env_profile["max_retries"]),
        )


task_evaluator_agent = TaskEvaluatorAgent()

