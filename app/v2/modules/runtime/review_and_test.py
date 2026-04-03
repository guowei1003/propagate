from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ReviewDecision:
    passed: bool
    summary: str
    issues: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TestDecision:
    passed: bool
    summary: str
    log_excerpt: str = ""
    fallback_used: bool = False


def evaluate_review(
    *,
    exit_code: int,
    stdout_text: str,
    stderr_text: str,
    output_files: list[str],
    review_policy: dict[str, bool] | None = None,
) -> ReviewDecision:
    policy = review_policy or {
        "artifact_required": True,
        "forbid_todo_markers": True,
        "require_clean_exit": True,
    }
    issues: list[str] = []
    combined = f"{stdout_text}\n{stderr_text}".lower()
    if policy.get("require_clean_exit", True) and exit_code != 0:
        issues.append("Execution returned non-zero exit code.")
    if policy.get("forbid_todo_markers", True) and "todo" in combined:
        issues.append("Execution output still contains TODO markers.")
    if policy.get("forbid_todo_markers", True) and "fixme" in combined:
        issues.append("Execution output still contains FIXME markers.")
    if policy.get("artifact_required", True) and not output_files:
        issues.append("Execution did not produce any output files.")
    passed = not issues
    summary = "Review passed." if passed else f"Review failed: {' '.join(issues)}"
    return ReviewDecision(passed=passed, summary=summary, issues=issues)


def evaluate_test(*, exit_code: int, stdout_text: str, stderr_text: str, test_command: str = "") -> TestDecision:
    combined = f"{stdout_text}\n{stderr_text}".lower()
    if exit_code != 0:
        return TestDecision(passed=False, summary="Test command failed.", log_excerpt=combined[:300], fallback_used=not bool(test_command))
    if "traceback" in combined or "error" in combined:
        return TestDecision(passed=False, summary="Test output contains failure markers.", log_excerpt=combined[:300], fallback_used=not bool(test_command))
    return TestDecision(passed=True, summary="Test passed.", log_excerpt=combined[:300], fallback_used=not bool(test_command))
