from __future__ import annotations

from fastapi import APIRouter

from app.v2.modules.tasks.schemas import ClarificationAnswerPayload, TaskCreatePayload
from app.v2.modules.tasks.service import task_service_v2


router = APIRouter(prefix="/v2/tasks", tags=["v2-tasks"])


@router.get("")
def list_tasks():
    return task_service_v2.list_tasks()


@router.post("")
def create_task(payload: TaskCreatePayload):
    return task_service_v2.create_task(payload)


@router.get("/{task_id}")
def get_task(task_id: str):
    return task_service_v2.get_task(task_id)


@router.post("/{task_id}/clarifications/{round_id}/answer")
def answer_clarification(task_id: str, round_id: str, payload: ClarificationAnswerPayload):
    return task_service_v2.answer_clarification(task_id, round_id, payload)
