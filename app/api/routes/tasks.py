from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse

from app.api.routes.dependencies import build_task_context, tasks
from app.repositories.subtask_repository import SubTaskRepository
from app.orchestrator.task_orchestrator import task_orchestrator


router = APIRouter()
subtasks = SubTaskRepository()


@router.get("/api/tasks")
def list_tasks() -> list[dict]:
    return tasks.list_tasks()


@router.get("/api/tasks/{task_id}")
def get_task(task_id: str) -> dict:
    context = build_task_context(task_id)
    if not context:
        raise HTTPException(status_code=404, detail="Task not found")
    return context


@router.get("/api/tasks/{task_id}/subtasks")
def list_subtasks(task_id: str) -> list[dict]:
    return subtasks.list_by_task(task_id)


@router.get("/api/subtasks/{subtask_id}")
def get_subtask(subtask_id: str) -> dict:
    subtask = subtasks.get_subtask(subtask_id)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return subtask


@router.post("/api/tasks")
def create_task_api(payload: dict) -> dict:
    title = payload.get("title", "").strip()
    prompt = payload.get("prompt", "").strip()
    env_profile_id = payload.get("env_profile_id")
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    task_id = task_orchestrator.create_task(title=title or None, prompt=prompt, env_profile_id=env_profile_id)
    return {"task_id": task_id}


@router.post("/tasks")
def create_task_form(
    prompt: str = Form(...),
    env_profile_id: str = Form(...),
) -> RedirectResponse:
    task_id = task_orchestrator.create_task(title=None, prompt=prompt.strip(), env_profile_id=env_profile_id)
    return RedirectResponse(url=f"/tasks/{task_id}", status_code=303)
