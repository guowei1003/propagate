from __future__ import annotations

import json
from typing import Any

from app.repositories.common import loads_json


STATUS_LABELS = {
    "CREATED": "已创建",
    "WAITING_USER_INPUT": "等待补充",
    "RUNNING": "执行中",
    "COMPLETED": "已完成",
    "PARTIAL_SUCCESS": "部分完成",
    "FAILED": "失败",
    "PENDING": "待执行",
    "READY": "就绪",
    "RETRY_PENDING": "待重试",
    "NEEDS_HUMAN_REVIEW": "需人工介入",
    "BLOCKED_BY_DEPENDENCY": "依赖阻塞",
    "answered": "已回答",
    "pending": "待回答",
}

PHASE_LABELS = {
    "REQUIREMENT_ANALYZING": "需求分析",
    "TASK_DECOMPOSING": "任务拆解",
    "TASK_EVALUATING": "执行评估",
    "SUBTASK_RUNNING": "子任务执行",
    "REPORTING": "报告生成",
    "DONE": "完成",
    "WAITING_USER_INPUT": "等待补充",
}

EVENT_LABELS = {
    "task.created": "任务创建",
    "requirement.analysis.completed": "需求分析完成",
    "requirement.analysis.failed": "需求分析失败",
    "requirement.clarification.requested": "发起需求澄清",
    "requirement.clarification.answered": "提交澄清回答",
    "task.decomposed": "任务拆解完成",
    "task.runtime.prepared": "运行环境准备完成",
    "subtask.ready": "子任务就绪",
    "subtask.started": "子任务开始",
    "subtask.completed": "子任务完成",
    "subtask.retrying": "子任务重试",
    "subtask.review.failed": "代码审查失败",
    "subtask.test.failed": "测试失败",
    "subtask.dependents.blocked": "依赖子任务阻塞",
    "task.report.generated": "最终报告生成",
}

ROLE_LABELS = {
    "assistant": "AI",
    "user": "用户",
    "tool": "Tool",
    "system": "系统",
}


def status_zh(value: str | None) -> str:
    if not value:
        return "-"
    return STATUS_LABELS.get(value, value)


def phase_zh(value: str | None) -> str:
    if not value:
        return "-"
    return PHASE_LABELS.get(value, value)


def event_zh(value: str | None) -> str:
    if not value:
        return "-"
    return EVENT_LABELS.get(value, value)


def role_zh(value: str | None) -> str:
    if not value:
        return "-"
    return ROLE_LABELS.get(value, value)


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def parse_event_payload(item: dict) -> dict:
    payload = loads_json(item.get("payload_json"), {})
    parsed = dict(item)
    parsed["payload"] = payload
    return parsed
