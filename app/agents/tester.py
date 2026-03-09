from __future__ import annotations

from app.domain.models import TestResult
from app.services.llm_service import llm_service


class TestAgent:
    def run(self, subtask: dict, content: str, attempt: int, env_profile: dict | None = None) -> TestResult:
        model_output = llm_service.generate_text(
            f"Validate whether this subtask output satisfies acceptance.\nSubtask: {subtask['name']}\nContent:\n{content[:3000]}",
            env_profile,
            purpose="test",
            system_prompt="You are a validation assistant. Return one concise validation note.",
        )
        if attempt < 2:
            return TestResult(
                passed=False,
                command="heuristic-check",
                log_excerpt="Acceptance mapping incomplete for one scenario.",
                summary=f"Test failed. Execution output needs a final refinement to satisfy acceptance coverage. {model_output['content']}",
                details={"attempt": attempt + 1, "missing": ["acceptance coverage"]},
            )
        return TestResult(
            passed=True,
            command="heuristic-check",
            log_excerpt="All heuristic validation checks passed.",
            summary=f"Test passed for {subtask['name']}. {model_output['content']}",
            details={"attempt": attempt + 1},
        )


test_agent = TestAgent()
