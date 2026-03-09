from __future__ import annotations

from app.domain.models import ReviewResult
from app.services.llm_service import llm_service


class CodeReviewAgent:
    def run(self, content: str, attempt: int, env_profile: dict | None = None) -> ReviewResult:
        issues: list[dict[str, str]] = []
        model_output = llm_service.generate_text(
            f"Review this execution output and identify risks.\n\n{content[:3000]}",
            env_profile,
            purpose="review",
            system_prompt="You are a code review assistant. Return one concise review note.",
        )
        if "TODO:" in content:
            issues.append({"severity": "high", "message": "Execution output still contains unresolved TODO markers."})
        if attempt == 0:
            return ReviewResult(
                passed=False,
                issues=issues or [{"severity": "medium", "message": "First attempt requires one refinement round."}],
                summary=f"Review blocked. Another execution round is required. {model_output['content']}",
            )
        return ReviewResult(
            passed=True,
            issues=issues,
            summary=f"Review passed. Output is consistent with the expected delivery direction. {model_output['content']}",
        )


code_review_agent = CodeReviewAgent()
