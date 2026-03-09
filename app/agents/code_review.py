from __future__ import annotations

import re

from app.domain.models import ReviewResult
from app.services.llm_service import llm_service


class CodeReviewAgent:
    """Review execution output based on content analysis, not hardcoded attempts."""

    CRITICAL_PATTERNS = [
        (r"TODO:", "high", "Unresolved TODO markers remain."),
        (r"FIXME:", "high", "Unresolved FIXME markers remain."),
        (r"XXX:", "medium", "XXX comment markers indicate potential issues."),
        (r"HACK:", "medium", "HACK markers indicate workaround code."),
        (r"raise NotImplemented", "high", "NotImplemented exception not handled."),
        (r"pass\s*$", "low", "Empty implementation (pass statement)."),
    ]

    def _analyze_content(self, content: str) -> list[dict[str, str]]:
        """Analyze content for common issues."""
        issues: list[dict[str, str]] = []
        for pattern, severity, message in self.CRITICAL_PATTERNS:
            if re.search(pattern, content, re.MULTILINE):
                issues.append({"severity": severity, "message": message})
        return issues

    def run(self, content: str, attempt: int, env_profile: dict | None = None) -> ReviewResult:
        issues = self._analyze_content(content)

        model_output = llm_service.generate_text(
            f"Review this execution output and identify risks. Respond with PASS or FAIL followed by reasoning.\n\n{content[:3000]}",
            env_profile,
            purpose="review",
            system_prompt="You are a code review assistant. Assess the output quality. Start with PASS or FAIL, then explain.",
        )

        # Check LLM response for pass/fail indicator
        model_content = model_output.get("content", "")
        model_suggests_fail = model_content.upper().startswith("FAIL")

        # High severity issues always fail
        has_critical_issues = any(i["severity"] == "high" for i in issues)

        # Combine content analysis with LLM judgment
        should_fail = has_critical_issues or model_suggests_fail

        if should_fail:
            if not issues:
                issues.append({"severity": "medium", "message": f"LLM review flagged issues: {model_content[:100]}"})
            return ReviewResult(
                passed=False,
                issues=issues,
                summary=f"Review failed. Issues found: {len(issues)}. {model_content[:200]}",
            )

        return ReviewResult(
            passed=True,
            issues=issues,
            summary=f"Review passed. {model_content[:200]}",
        )


code_review_agent = CodeReviewAgent()
