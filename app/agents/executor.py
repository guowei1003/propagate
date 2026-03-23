from __future__ import annotations

import time
from pathlib import Path

from app.domain.models import ExecutionResult
from app.services.llm_service import llm_service


class ExecutorAgent:
    def _persist_runtime_output(self, workspace_path: str | None, attempt: int, content: str) -> str | None:
        if not workspace_path:
            return None
        workspace = Path(workspace_path)
        workspace.mkdir(parents=True, exist_ok=True)
        output_path = workspace / f"agent-output-attempt-{attempt + 1}.md"
        output_path.write_text(content, encoding="utf-8")
        return str(output_path)

    def run(self, task: dict, subtask: dict, requirement: dict, attempt: int, env_profile: dict | None = None) -> ExecutionResult:
        time.sleep(0.3)
        runtime_context = subtask.get("input_context", {}).get("runtime", {})
        runtime_workspace = runtime_context.get("workspace_path")
        runtime_agent_name = runtime_context.get("agent_name", subtask.get("agent_template"))
        runtime_skills = ", ".join(subtask.get("skill_bindings", []))
        model_output = llm_service.generate_text(
            (
                f"Task: {task['title']}\n"
                f"Subtask: {subtask['name']}\n"
                f"Description: {subtask['description']}\n"
                f"Acceptance: {subtask['acceptance']}\n"
                f"Runtime Agent: {runtime_agent_name}\n"
                f"Skills: {runtime_skills}"
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
            "## Runtime Agent",
            runtime_agent_name,
            "",
            "## Skills",
            runtime_skills or "none",
            "",
            "## Isolated Workspace",
            runtime_workspace or "not configured",
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
        runtime_output_path = self._persist_runtime_output(runtime_workspace, attempt, content)
        summary = f"{subtask['name']} execution attempt {attempt + 1} completed."
        metadata = {
            "attempt": attempt + 1,
            "category": subtask["category"],
            "provider_type": model_output["provider_type"],
            "model": model_output["model"],
            "runtime_agent": runtime_agent_name,
            "runtime_workspace": runtime_workspace,
            "runtime_output_path": runtime_output_path,
        }
        return ExecutionResult(content=content, summary=summary, metadata=metadata)


executor_agent = ExecutorAgent()
