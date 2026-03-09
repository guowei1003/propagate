from __future__ import annotations

import uuid

from app.agents.reporter import report_agent
from app.agents.requirement_analyzer import requirement_analyzer_agent
from app.agents.task_decomposer import task_decomposer_agent
from app.agents.task_evaluator import task_evaluator_agent
from app.enums import (
    SUBTASK_STATUS_COMPLETED,
    SUBTASK_STATUS_PENDING,
    TASK_PHASE_DONE,
    TASK_PHASE_REPORTING,
    TASK_PHASE_REQUIREMENT_ANALYZING,
    TASK_PHASE_SUBTASK_RUNNING,
    TASK_PHASE_TASK_DECOMPOSING,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_PARTIAL_SUCCESS,
    TASK_STATUS_RUNNING,
    TASK_STATUS_WAITING_USER_INPUT,
)
from app.repositories.clarification_repository import ClarificationRepository
from app.repositories.env_profile_repository import EnvProfileRepository
from app.repositories.event_repository import EventRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.subtask_repository import SubTaskRepository
from app.repositories.task_repository import TaskRepository
from app.services.artifact_service import artifact_service
from app.services.event_service import event_service


class TaskOrchestrator:
    def __init__(self) -> None:
        self.tasks = TaskRepository()
        self.requirements = RequirementRepository()
        self.clarifications = ClarificationRepository()
        self.subtasks = SubTaskRepository()
        self.events = EventRepository()
        self.reports = ReportRepository()
        self.env_profiles = EnvProfileRepository()

    def create_task(self, title: str, prompt: str, env_profile_id: str | None = None) -> str:
        profile = (
            self.env_profiles.get_profile_for_runtime(env_profile_id)
            if env_profile_id
            else self.env_profiles.get_default_profile_for_runtime()
        )
        if not profile:
            raise ValueError("No environment profile available.")
        task_id = self.tasks.create_task(title=title, prompt=prompt, env_profile_id=profile["id"])
        event_service.publish(task_id, "task.created", "Task created.")
        self.start_requirement_analysis(task_id)
        return task_id

    def start_requirement_analysis(self, task_id: str) -> None:
        task = self.tasks.get_task(task_id)
        if not task:
            return
        env_profile = self.env_profiles.get_profile_for_runtime(task["env_profile_id"])
        self.tasks.update_task(
            task_id,
            status=TASK_STATUS_RUNNING,
            current_phase=TASK_PHASE_REQUIREMENT_ANALYZING,
        )
        answers = self.clarifications.get_merged_answers(task_id)
        analysis = requirement_analyzer_agent.run(task["prompt"], answers, env_profile)
        self.requirements.save_requirement(
            task_id,
            {
                "goal": analysis.goal,
                "scope": analysis.scope,
                "inputs": analysis.inputs,
                "outputs": analysis.outputs,
                "constraints": analysis.constraints,
                "acceptance": analysis.acceptance,
                "missing_info": analysis.missing_info,
            },
        )
        event_service.publish(task_id, "requirement.analysis.completed", "Requirement analysis completed.")
        if analysis.missing_info:
            self.clarifications.create_round(task_id, analysis.missing_info)
            self.tasks.update_task(
                task_id,
                status=TASK_STATUS_WAITING_USER_INPUT,
                current_phase=TASK_STATUS_WAITING_USER_INPUT,
            )
            event_service.publish(
                task_id,
                "requirement.clarification.requested",
                f"{len(analysis.missing_info)} clarification questions generated.",
                level="warn",
            )
            return
        self.decompose_task(task_id)

    def submit_clarification_answers(self, task_id: str, round_id: str, answers: dict[str, str]) -> None:
        self.clarifications.answer_round(round_id, answers)
        event_service.publish(task_id, "requirement.clarification.answered", "Clarification answers submitted.")
        self.start_requirement_analysis(task_id)

    def decompose_task(self, task_id: str) -> None:
        task = self.tasks.get_task(task_id)
        requirement = self.requirements.get_latest(task_id)
        if not task or not requirement:
            return
        self.tasks.update_task(task_id, status=TASK_STATUS_RUNNING, current_phase=TASK_PHASE_TASK_DECOMPOSING)
        env_profile = self.env_profiles.get_profile_for_runtime(task["env_profile_id"])
        decomposed = task_decomposer_agent.run(task, requirement, env_profile)
        items: list[dict] = []
        dependencies: list[tuple[str, str]] = []
        subtask_ids: list[str] = []
        for index, subtask in enumerate(decomposed):
            plan = task_evaluator_agent.run(subtask, env_profile)
            subtask_id = str(uuid.uuid4())
            subtask_ids.append(subtask_id)
            items.append(
                {
                    "id": subtask_id,
                    "name": subtask.name,
                    "description": subtask.description,
                    "category": subtask.category,
                    "priority": subtask.priority,
                    "sequence_no": index,
                    "agent_template": plan.agent_template,
                    "skill_bindings": plan.skills,
                    "acceptance": subtask.acceptance,
                    "input_context": {
                        "task_prompt": task["prompt"],
                        "requirement_goal": requirement["goal"],
                    },
                    "timeout_sec": plan.timeout_sec,
                    "max_retries": plan.max_retries,
                }
            )
        for index, subtask in enumerate(decomposed):
            for dep_index in subtask.depends_on:
                dependencies.append((subtask_ids[dep_index], subtask_ids[index]))
        self.subtasks.replace_subtasks(task_id, items, dependencies)
        event_service.publish(task_id, "task.decomposed", f"Created {len(items)} subtasks.")
        self.refresh_ready_subtasks(task_id)
        self.tasks.update_task(task_id, status=TASK_STATUS_RUNNING, current_phase=TASK_PHASE_SUBTASK_RUNNING)

    def refresh_ready_subtasks(self, task_id: str) -> None:
        subtasks = self.subtasks.list_by_task(task_id)
        dependencies = self.subtasks.list_dependencies(task_id)
        completed = {item["id"] for item in subtasks if item["status"] == SUBTASK_STATUS_COMPLETED}
        for subtask in subtasks:
            if subtask["status"] != SUBTASK_STATUS_PENDING:
                continue
            blockers = [dep["from_sub_task_id"] for dep in dependencies if dep["to_sub_task_id"] == subtask["id"]]
            if all(blocker in completed for blocker in blockers):
                self.subtasks.mark_ready(subtask["id"])
                event_service.publish(
                    task_id,
                    "subtask.ready",
                    f"{subtask['name']} is ready to run.",
                    sub_task_id=subtask["id"],
                )
        progress = self.subtasks.get_task_progress(task_id)
        self.tasks.update_task(task_id, progress_percent=progress)

    def finalize_task_if_done(self, task_id: str) -> None:
        task = self.tasks.get_task(task_id)
        requirement = self.requirements.get_latest(task_id)
        subtasks = self.subtasks.list_by_task(task_id)
        if not task or not requirement or not subtasks:
            return
        terminal = all(item["status"] in {"COMPLETED", "NEEDS_HUMAN_REVIEW"} for item in subtasks)
        if not terminal:
            self.refresh_ready_subtasks(task_id)
            return
        self.tasks.update_task(task_id, current_phase=TASK_PHASE_REPORTING, progress_percent=self.subtasks.get_task_progress(task_id))
        events = self.events.list_by_task(task_id, limit=1000)
        env_profile = self.env_profiles.get_profile_for_runtime(task["env_profile_id"])
        markdown, summary = report_agent.run(task, requirement, subtasks, events, env_profile)
        self.reports.save_report(task_id, markdown, summary)
        artifact_service.save_text_artifact(
            task_id=task_id,
            sub_task_id=None,
            artifact_type="report",
            filename="final-report.md",
            content=markdown,
            summary="Final task report",
            metadata=summary,
        )
        status = TASK_STATUS_COMPLETED if all(item["status"] == "COMPLETED" for item in subtasks) else TASK_STATUS_PARTIAL_SUCCESS
        self.tasks.update_task(
            task_id,
            status=status,
            current_phase=TASK_PHASE_DONE,
            progress_percent=self.subtasks.get_task_progress(task_id),
            completed=True,
        )
        event_service.publish(task_id, "task.report.generated", "Final report generated.")


task_orchestrator = TaskOrchestrator()
