from __future__ import annotations


READY_CANDIDATE_STATUSES = {"PENDING", "RETRY_PENDING"}
FAILED_BLOCKING_STATUSES = {"NEEDS_HUMAN_REVIEW", "BLOCKED_BY_DEPENDENCY"}


def compute_ready_subtasks(subtasks: list[dict], dependencies: list[dict]) -> list[str]:
    completed = {item["id"] for item in subtasks if item["status"] == "COMPLETED"}
    ready: list[str] = []
    for subtask in subtasks:
        if subtask["status"] not in READY_CANDIDATE_STATUSES:
            continue
        blockers = [
            dep["from_sub_task_id"]
            for dep in dependencies
            if dep["to_sub_task_id"] == subtask["id"]
        ]
        if all(blocker in completed for blocker in blockers):
            ready.append(subtask["id"])
    return ready


def block_dependents(subtasks: list[dict], dependencies: list[dict], *, failed_subtask_id: str) -> list[str]:
    status_by_id = {item["id"]: item["status"] for item in subtasks}
    blocked: list[str] = []
    queue = [failed_subtask_id]
    while queue:
        current = queue.pop(0)
        for dep in dependencies:
            if dep["from_sub_task_id"] != current:
                continue
            downstream = dep["to_sub_task_id"]
            status = status_by_id.get(downstream)
            if status in FAILED_BLOCKING_STATUSES or status == "COMPLETED":
                continue
            status_by_id[downstream] = "BLOCKED_BY_DEPENDENCY"
            blocked.append(downstream)
            queue.append(downstream)
    return blocked
