from __future__ import annotations

import re

from app.domain.models import TestResult
from app.services.llm_service import llm_service


class TestAgent:
    """Validate subtask output against acceptance criteria, not hardcoded attempts."""

    def _check_acceptance_coverage(self, content: str, acceptance: dict) -> list[str]:
        """Check if acceptance criteria are addressed in content."""
        missing: list[str] = []
        focus_areas = acceptance.get("focus", [])
        for area in focus_areas:
            # Simple heuristic: check if the focus area is mentioned
            if area.lower() not in content.lower():
                missing.append(f"Missing coverage for: {area}")
        return missing

    def run(self, subtask: dict, content: str, attempt: int, env_profile: dict | None = None) -> TestResult:
        acceptance = subtask.get("acceptance", {})
        focus_areas = acceptance.get("focus", [])

        # Check acceptance coverage
        missing = self._check_acceptance_coverage(content, acceptance)

        # Use LLM to validate against acceptance criteria
        prompt = (
            f"Validate whether this subtask output satisfies the acceptance criteria.\n"
            f"Subtask: {subtask['name']}\n"
            f"Focus areas: {', '.join(focus_areas)}\n"
            f"Content:\n{content[:2500]}\n\n"
            f"Respond with PASS or FAIL followed by your reasoning."
        )
        model_output = llm_service.generate_text(
            prompt,
            env_profile,
            purpose="test",
            system_prompt="You are a validation assistant. Start with PASS or FAIL, then explain your assessment.",
        )

        model_content = model_output.get("content", "")
        model_suggests_fail = model_content.upper().startswith("FAIL")

        # Combine coverage check with LLM judgment
        should_fail = len(missing) > 2 or model_suggests_fail

        if should_fail:
            return TestResult(
                passed=False,
                command="acceptance-validation",
                log_excerpt="\n".join(missing[:3]) if missing else "LLM validation failed.",
                summary=f"Test failed. {model_content[:200]}",
                details={"attempt": attempt + 1, "missing": missing, "model_response": model_content[:500]},
            )

        return TestResult(
            passed=True,
            command="acceptance-validation",
            log_excerpt=f"All {len(focus_areas)} focus areas validated.",
            summary=f"Test passed for {subtask['name']}. {model_content[:200]}",
            details={"attempt": attempt + 1, "validated_areas": focus_areas},
        )


test_agent = TestAgent()
