from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.api.routes.dependencies import clarifications
from app.orchestrator.task_orchestrator import task_orchestrator


router = APIRouter()


@router.post("/tasks/{task_id}/clarifications/{round_id}")
async def submit_clarification_form(request: Request, task_id: str, round_id: str) -> RedirectResponse:
    form = await request.form()
    answers: dict[str, str] = {}
    for key, value in form.items():
        if key.startswith("answer__"):
            answers[key.split("answer__", 1)[1]] = str(value).strip()
    if not answers:
        raise HTTPException(status_code=400, detail="No clarification answers provided")
    task_orchestrator.submit_clarification_answers(task_id, round_id, answers)
    return RedirectResponse(url=f"/tasks/{task_id}", status_code=303)


@router.post("/api/tasks/{task_id}/clarifications/{round_id}")
def submit_clarification_api(task_id: str, round_id: str, payload: dict) -> dict:
    answers = payload.get("answers", {})
    if not isinstance(answers, dict) or not answers:
        raise HTTPException(status_code=400, detail="answers must be a non-empty object")
    if not clarifications.get_pending_round(task_id):
        raise HTTPException(status_code=400, detail="No pending clarification round")
    task_orchestrator.submit_clarification_answers(task_id, round_id, answers)
    return {"ok": True}

