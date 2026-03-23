from __future__ import annotations

from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.clarification_repository import ClarificationRepository
from app.repositories.common import loads_json
from app.repositories.env_profile_repository import EnvProfileRepository
from app.repositories.event_repository import EventRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.subtask_repository import SubTaskRepository
from app.repositories.task_repository import TaskRepository
from app.services.view_service import event_zh, role_zh


tasks = TaskRepository()
requirements = RequirementRepository()
clarifications = ClarificationRepository()
subtasks = SubTaskRepository()
events = EventRepository()
reports = ReportRepository()
artifacts = ArtifactRepository()
env_profiles = EnvProfileRepository()


def _conversation_item(
    *,
    role: str,
    kind: str,
    title: str,
    content: str,
    created_at: str | None = None,
    tool_name: str | None = None,
    tool_input: dict | None = None,
) -> dict:
    return {
        "role": role,
        "role_label": role_zh(role),
        "kind": kind,
        "title": title,
        "content": content,
        "created_at": created_at,
        "tool_name": tool_name,
        "tool_input": tool_input or {},
    }


def _build_conversation(task: dict, requirement: dict | None, rounds: list[dict], event_items: list[dict]) -> list[dict]:
    items: list[dict] = []
    items.append(
        _conversation_item(
            role="assistant",
            kind="message",
            title="AI 需求助手",
            content="请描述你的目标，我会逐步追问缺失信息，并在准备完成后自动进入任务执行。",
            created_at=task.get("created_at"),
        )
    )
    items.append(
        _conversation_item(
            role="user",
            kind="message",
            title="初始需求",
            content=task.get("prompt", ""),
            created_at=task.get("created_at"),
        )
    )

    for round_item in rounds:
        questions = round_item.get("questions", [])
        if questions:
            question_text = "\n".join([f"{idx + 1}. {q['question']}" for idx, q in enumerate(questions)])
            items.append(
                _conversation_item(
                    role="assistant",
                    kind="message",
                    title="需求澄清",
                    content=question_text,
                    created_at=round_item.get("created_at"),
                )
            )
        answers = round_item.get("answers", {})
        if answers:
            answer_text = "\n".join([f"- {key}: {value}" for key, value in answers.items()])
            items.append(
                _conversation_item(
                    role="user",
                    kind="message",
                    title="补充信息",
                    content=answer_text,
                    created_at=round_item.get("answered_at"),
                )
            )

    if requirement:
        deliverable = requirement.get("outputs", {}).get("primary_deliverable", "待澄清")
        must_have = requirement.get("acceptance", {}).get("must_have", [])
        summary = "\n".join(
            [
                f"目标：{requirement.get('goal', '')}",
                f"范围：{requirement.get('scope', '')}",
                f"交付：{deliverable}",
                "验收：",
                *[f"- {item}" for item in must_have],
            ]
        )
        items.append(
            _conversation_item(
                role="assistant",
                kind="message",
                title="需求摘要",
                content=summary,
                created_at=requirement.get("created_at"),
            )
        )

    for event_item in event_items:
        event_type = event_item.get("event_type")
        payload = event_item.get("payload", {})
        if event_type == "task.runtime.prepared":
            for agent in payload.get("agents", []):
                items.append(
                    _conversation_item(
                        role="assistant",
                        kind="tool_call",
                        title="callTool",
                        content="创建临时执行 Agent 并绑定技能。",
                        created_at=event_item.get("created_at"),
                        tool_name="create_sub_agent",
                        tool_input={
                            "agent_name": agent.get("agent_name"),
                            "skills": agent.get("skills", []),
                            "sandbox_mode": agent.get("sandbox_mode"),
                            "subtask_id": agent.get("subtask_id"),
                        },
                    )
                )
        elif event_type in {
            "subtask.started",
            "subtask.completed",
            "subtask.retrying",
            "subtask.review.failed",
            "subtask.test.failed",
            "subtask.dependents.blocked",
            "task.report.generated",
        }:
            items.append(
                _conversation_item(
                    role="tool",
                    kind="tool_result",
                    title=event_zh(event_type),
                    content=event_item.get("message", ""),
                    created_at=event_item.get("created_at"),
                    tool_name=event_type,
                    tool_input=payload,
                )
            )

    return items


def build_task_context(task_id: str) -> dict | None:
    task = tasks.get_task(task_id)
    if not task:
        return None
    requirement = requirements.get_latest(task_id)
    round_items = clarifications.list_rounds(task_id)
    event_items = events.list_by_task(task_id, limit=200)
    parsed_events = []
    for item in event_items:
        payload = loads_json(item.get("payload_json"), {})
        parsed = dict(item)
        parsed["payload"] = payload
        parsed_events.append(parsed)

    return {
        "task": task,
        "requirement": requirement,
        "pending_round": clarifications.get_pending_round(task_id),
        "clarification_rounds": round_items,
        "subtasks": subtasks.list_by_task(task_id),
        "events": parsed_events,
        "report": reports.get_report(task_id),
        "artifacts": artifacts.list_by_task(task_id),
        "env_profile": env_profiles.get_profile(task["env_profile_id"]),
        "conversation": _build_conversation(task, requirement, round_items, parsed_events),
    }
