from __future__ import annotations

from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.clarification_repository import ClarificationRepository
from app.repositories.env_profile_repository import EnvProfileRepository
from app.repositories.event_repository import EventRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.subtask_repository import SubTaskRepository
from app.repositories.task_repository import TaskRepository


tasks = TaskRepository()
requirements = RequirementRepository()
clarifications = ClarificationRepository()
subtasks = SubTaskRepository()
events = EventRepository()
reports = ReportRepository()
artifacts = ArtifactRepository()
env_profiles = EnvProfileRepository()


def build_task_context(task_id: str) -> dict | None:
    task = tasks.get_task(task_id)
    if not task:
        return None
    return {
        "task": task,
        "requirement": requirements.get_latest(task_id),
        "pending_round": clarifications.get_pending_round(task_id),
        "clarification_rounds": clarifications.list_rounds(task_id),
        "subtasks": subtasks.list_by_task(task_id),
        "events": events.list_by_task(task_id, limit=200),
        "report": reports.get_report(task_id),
        "artifacts": artifacts.list_by_task(task_id),
        "env_profile": env_profiles.get_profile(task["env_profile_id"]),
    }

