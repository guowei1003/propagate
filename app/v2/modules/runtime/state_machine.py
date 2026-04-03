from __future__ import annotations


TERMINAL_STATUSES = {"COMPLETED", "NEEDS_HUMAN_REVIEW", "BLOCKED_BY_DEPENDENCY"}


def derive_run_status_and_phase(subtasks: list[dict], *, all_success: bool) -> tuple[str, str]:
    statuses = [item["status"] for item in subtasks]
    if statuses and all(status == "COMPLETED" for status in statuses):
        return "COMPLETED", "DONE"
    if statuses and all(status in TERMINAL_STATUSES for status in statuses):
        return "PARTIAL_SUCCESS", "DONE"
    return ("RUNNING", "SUBTASK_RUNNING") if not all_success or statuses else ("RUNNING", "SUBTASK_RUNNING")
