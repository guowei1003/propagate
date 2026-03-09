from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RequirementAnalysis:
    goal: str
    scope: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    constraints: dict[str, Any]
    acceptance: dict[str, Any]
    missing_info: list[dict[str, str]]


@dataclass
class ClarificationRound:
    id: str
    task_id: str
    status: str
    questions: list[dict[str, str]]
    answers: dict[str, str]


@dataclass
class DecomposedSubtask:
    name: str
    description: str
    category: str
    priority: int
    depends_on: list[int]
    acceptance: dict[str, Any]


@dataclass
class ExecutionPlan:
    agent_template: str
    skills: list[str]
    timeout_sec: int
    max_retries: int


@dataclass
class ExecutionResult:
    content: str
    summary: str
    metadata: dict[str, Any]


@dataclass
class ReviewResult:
    passed: bool
    issues: list[dict[str, str]]
    summary: str


@dataclass
class TestResult:
    passed: bool
    command: str
    log_excerpt: str
    summary: str
    details: dict[str, Any]

