from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.routes.dependencies import build_task_context, env_profiles, tasks
from app.config import BASE_DIR


router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "web" / "templates"))


@router.get("/", response_class=HTMLResponse)
def home() -> RedirectResponse:
    return RedirectResponse(url="/tasks", status_code=302)


@router.get("/tasks", response_class=HTMLResponse)
def task_list_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        name="tasks/list.html",
        request=request,
        context={
            "tasks": tasks.list_tasks(),
            "env_profiles": env_profiles.list_profiles(),
            "page_title": "Tasks",
        },
    )


@router.get("/tasks/{task_id}", response_class=HTMLResponse)
def task_detail_page(request: Request, task_id: str) -> HTMLResponse:
    context = build_task_context(task_id)
    if not context:
        raise HTTPException(status_code=404, detail="Task not found")
    context.update(
        {
            "page_title": context["task"]["title"],
        }
    )
    return templates.TemplateResponse(
        name="tasks/detail.html",
        request=request,
        context=context,
    )


@router.get("/env-profiles", response_class=HTMLResponse)
def env_profiles_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        name="env_profiles/list.html",
        request=request,
        context={
            "env_profiles": env_profiles.list_profiles(),
            "page_title": "Environment Profiles",
        },
    )
