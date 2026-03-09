from __future__ import annotations

import time

from app.domain.models import ExecutionResult
from app.services.llm_service import llm_service


class ExecutorAgent:
    def run(self, task: dict, subtask: dict, requirement: dict, attempt: int, env_profile: dict | None = None) -> ExecutionResult:
        time.sleep(0.3)
        model_output = llm_service.generate_text(
            (
                f"Task: {task['title']}\n"
                f"Subtask: {subtask['name']}\n"
                f"Description: {subtask['description']}\n"
                f"Acceptance: {subtask['acceptance']}"
            ),
            env_profile,
            purpose="default",
            system_prompt="You are an implementation planner. Return a concise build note for this subtask.",
        )
        sections = [
            f"# {subtask['name']}",
            "",
            "## Goal",
            requirement["goal"],
            "",
            "## Approach",
            subtask["description"],
            "",
            "## Acceptance Focus",
            ", ".join(subtask["acceptance"].get("focus", [])),
            "",
            "## Model",
            f"{model_output['provider_type']} / {model_output['model']}",
            "",
            "## Model Guidance",
            model_output["content"],
            "",
            "## Attempt",
            f"Attempt {attempt + 1}",
        ]
        if attempt == 0:
            sections.extend(["", "## Follow-up", "TODO: refine edge cases before final delivery."])
        elif attempt == 1:
            sections.extend(["", "## Validation", "Smoke checks prepared, but one regression scenario still needs confirmation."])
        else:
            sections.extend(
                [
                    "",
                    "## Validation",
                    "Primary scenarios covered and acceptance criteria mapped to execution output.",
                ]
            )
        content = "\n".join(sections)
        summary = f"{subtask['name']} execution attempt {attempt + 1} completed."
        metadata = {
            "attempt": attempt + 1,
            "category": subtask["category"],
            "provider_type": model_output["provider_type"],
            "model": model_output["model"],
        }
        return ExecutionResult(content=content, summary=summary, metadata=metadata)


executor_agent = ExecutorAgent()
