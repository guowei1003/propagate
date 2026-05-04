from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.harness.compiler import compile_execution_plan
from app.harness.contracts import MissionBrief
from app.harness.memory import remember
from app.harness.policies import step_requires_approval
from app.harness.selector import select_agents_for_task
from app.harness.supervisor import evaluate_step
from app.models.artifact import Artifact
from app.models.profile import Profile
from app.models.run import RunStep, TaskRun
from app.providers.base import ProviderContext
from app.providers.mock import MockProvider
from app.providers.openai_responses import OpenAIResponsesProvider
from app.services.approval_service import approval_service
from app.services.stream_service import stream_service
from app.tools.http_allowlist import call_allowlisted_url
from app.tools.sandbox_python import run_python_script
from app.tools.sandbox_shell import run_shell_commands


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RunService:
    def __init__(self) -> None:
        self._mock = MockProvider()
        self._openai: OpenAIResponsesProvider | None = None

    def _provider_for(self, provider_name: str):
        if provider_name == "openai":
            if self._openai is None:
                self._openai = OpenAIResponsesProvider()
            return self._openai
        return self._mock

    async def get_run(self, session: AsyncSession, task_id: UUID, run_id: UUID) -> TaskRun | None:
        result = await session.execute(
            select(TaskRun)
            .options(
                selectinload(TaskRun.task),
                selectinload(TaskRun.steps),
                selectinload(TaskRun.events),
                selectinload(TaskRun.approvals),
                selectinload(TaskRun.artifacts),
            )
            .where(TaskRun.id == run_id, TaskRun.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def start_run(self, session: AsyncSession, task, run: TaskRun) -> TaskRun:
        profile = await self._resolve_profile(session, run.profile_id)
        provider_name = profile.model_provider if profile else "mock"
        context = ProviderContext(
            provider=provider_name,
            model=(profile.model_name if profile else "gpt-4.1-mini"),
            temperature=(profile.temperature if profile else 0.1),
            max_tokens=(profile.max_tokens if profile else 4000),
        )
        provider = self._provider_for(provider_name)

        run.status = "running"
        run.started_at = utcnow()
        await stream_service.append_event(
            session,
            run.id,
            category="run",
            name="run_started",
            message="任务运行开始",
            payload={"task_id": str(task.id)},
        )

        mission = await provider.build_mission(
            {
                "goal": task.goal,
                "constraints": task.constraints,
                "deliverables": task.deliverables,
                "approval_mode": task.approval_mode,
            },
            context,
        )
        run.mission = mission.model_dump()
        run.memory = remember(run.memory, "mission", mission.model_dump())

        selection = select_agents_for_task(task.goal, mission.constraints, mission.deliverables)
        run.warnings = selection.warnings
        selected_agents = [agent.model_dump() for agent in selection.agents]
        run.selected_agents = selected_agents
        await stream_service.append_event(
            session,
            run.id,
            category="planner",
            name="agents_selected",
            message="已自动选择任务所需智能体",
            payload={"agents": selected_agents, "warnings": selection.warnings},
        )

        plan = await compile_execution_plan(mission, selected_agents, provider, context)
        run.selected_agents = [agent.model_dump() for agent in plan.selected_agents]
        run.execution_plan = plan.model_dump()
        run.memory = remember(run.memory, "current_plan", plan.model_dump())
        await stream_service.append_event(
            session,
            run.id,
            category="planner",
            name="plan_compiled",
            message="执行计划已生成",
            payload={
                "steps": [step.model_dump() for step in plan.steps],
                "selected_agents": run.selected_agents,
            },
        )

        for position, step in enumerate(plan.steps):
            step_dict = step.model_dump()
            step_dict["approval_required"] = step_requires_approval(
                step,
                mission,
                {
                    "requires_human_approval_for_high_risk": profile.requires_human_approval_for_high_risk,
                }
                if profile
                else None,
            )
            run_step = RunStep(
                run_id=run.id,
                step_id=step.id,
                position=position,
                title=step.title,
                kind=step.kind,
                assigned_agent_id=step.assigned_agent_id,
                instructions=step.instructions,
                approval_required=step_dict["approval_required"],
                max_retries=step.max_retries,
                timeout_sec=step.timeout_sec,
                dependencies=step.depends_on,
                expected_artifacts=step.expected_artifacts,
                status="pending",
            )
            session.add(run_step)
        await session.flush()
        await session.refresh(run, ["steps", "approvals", "artifacts"])
        await self._execute_pending_steps(session, run, mission, provider, context, profile)
        await session.commit()
        return run

    async def _resolve_profile(self, session: AsyncSession, profile_id) -> Profile | None:
        if profile_id is None:
            return None
        return await session.get(Profile, profile_id)

    async def _execute_pending_steps(self, session, run, mission, provider, context, profile):
        steps = list(run.steps)
        for step in steps:
            if step.status != "pending":
                continue
            if step.approval_required:
                await approval_service.request_approval(
                    session,
                    run.id,
                    step.step_id,
                    f"步骤 {step.title} 需要人工审批后继续",
                )
                step.status = "waiting_approval"
                run.status = "waiting_approval"
                await stream_service.append_event(
                    session,
                    run.id,
                    category="approval",
                    name="approval_requested",
                    message=f"{step.title} 等待审批",
                    payload={"step_id": step.step_id},
                )
                break

            await self._execute_step(session, run, step, mission, provider, context, profile)
            if step.status != "completed":
                break

        if all(step.status in {"completed", "skipped"} for step in run.steps):
            await self._finalize_run(session, run, mission, provider, context)

    async def _execute_step(self, session, run, step, mission, provider, context, profile):
        step.status = "running"
        step.attempts += 1
        await stream_service.append_event(
            session,
            run.id,
            category="step",
            name="step_started",
            message=f"开始执行步骤 {step.title}",
            payload={"step_id": step.step_id, "kind": step.kind},
        )

        if step.kind == "sandbox_python":
            result = await run_python_script(
                str(run.id),
                "print('propagate mock python step')",
                step.timeout_sec,
            )
        elif step.kind == "sandbox_shell":
            result = await run_shell_commands(
                str(run.id),
                "echo propagate mock shell step",
                step.timeout_sec,
            )
        elif step.kind == "http":
            allowed_domains = profile.http_allowlist_domains if profile else []
            allowed_methods = profile.http_allowlist_methods if profile else ["GET", "POST"]
            if not allowed_domains:
                result = await call_allowlisted_url(
                    "https://example.com",
                    "GET",
                    allowed_domains=allowed_domains,
                    allowed_methods=allowed_methods,
                )
            else:
                result = await call_allowlisted_url(
                    f"https://{allowed_domains[0]}",
                    allowed_methods[0],
                    allowed_domains=allowed_domains,
                    allowed_methods=allowed_methods,
                )
        else:
            result = type("Obj", (), {
                "status": "completed",
                "summary": "analysis/report step completed",
                "artifacts": [],
                "payload": {"status": "completed", "summary": "analysis/report step completed"},
            })()

        payload = result.payload if hasattr(result, "payload") else result
        payload["status"] = getattr(result, "status", payload.get("status", "completed"))
        payload["summary"] = getattr(result, "summary", payload.get("summary", "completed"))
        payload["artifacts"] = getattr(result, "artifacts", payload.get("artifacts", []))
        payload["attempts"] = step.attempts
        step.result = payload
        await self._record_artifacts(session, run.id, step.step_id, payload)

        assessment = await evaluate_step(
            mission,
            {
                "step_id": step.step_id,
                "max_retries": step.max_retries,
                "approval_required": step.approval_required,
            },
            payload,
            provider,
            context,
        )

        if assessment.status == "advance":
            step.status = "completed"
        elif assessment.status == "retry" and step.attempts <= step.max_retries:
            step.status = "pending"
        elif assessment.status == "replan":
            run.status = "needs_replan"
            step.status = "failed"
        else:
            step.status = "failed"
            run.status = "failed"

        await stream_service.append_event(
            session,
            run.id,
            category="step",
            name="step_finished",
            message=f"步骤 {step.title} 执行结束",
            payload={"step_id": step.step_id, "result": payload, "assessment": assessment.model_dump()},
        )

        if step.status == "pending":
            await self._execute_step(session, run, step, mission, provider, context, profile)

    async def _finalize_run(self, session, run, mission, provider, context):
        verification = await provider.verify(
            mission,
            None,
            {
                "status": "completed",
                "summary": "run completed",
                "artifacts": [artifact.name for artifact in run.artifacts],
            },
            context,
        )
        run.verification_summary = verification.model_dump()
        run.status = "completed" if verification.passed else "failed"
        run.completed_at = utcnow()
        await stream_service.append_event(
            session,
            run.id,
            category="run",
            name="run_finished",
            message="任务运行结束",
            payload={"status": run.status, "verification": verification.model_dump()},
        )

    async def _record_artifacts(self, session: AsyncSession, run_id, step_id: str, result: dict) -> None:
        artifact_names = result.get("artifacts", [])
        for name in artifact_names:
            artifact = Artifact(
                run_id=run_id,
                step_id=step_id,
                name=name,
                artifact_type="generated",
                mime_type="text/plain",
                storage_path=f"{run_id}/{name}",
                sha256="mock",
                details={"source": "mock-tool"},
            )
            session.add(artifact)

    async def resume_run(self, session: AsyncSession, task_id: UUID, run_id: UUID) -> TaskRun:
        run = await self.get_run(session, task_id, run_id)
        if run is None:
            raise ValueError("run not found")
        for approval in run.approvals:
            if approval.status == "approved":
                for step in run.steps:
                    if step.step_id == approval.step_id and step.status == "waiting_approval":
                        step.status = "pending"
        run.status = "running"
        task = run.task
        profile = await self._resolve_profile(session, run.profile_id)
        provider_name = profile.model_provider if profile else "mock"
        context = ProviderContext(
            provider=provider_name,
            model=(profile.model_name if profile else "gpt-4.1-mini"),
            temperature=(profile.temperature if profile else 0.1),
            max_tokens=(profile.max_tokens if profile else 4000),
        )
        provider = self._provider_for(provider_name)

        await self._execute_pending_steps(
            session,
            run,
            MissionBrief.model_validate(run.mission),
            provider,
            context,
            profile,
        )
        await session.commit()
        return run

    async def cancel_run(self, session: AsyncSession, task_id: UUID, run_id: UUID) -> TaskRun:
        run = await self.get_run(session, task_id, run_id)
        if run is None:
            raise ValueError("run not found")
        run.status = "canceled"
        run.canceled_at = utcnow()
        await stream_service.append_event(
            session,
            run.id,
            category="run",
            name="run_canceled",
            message="任务运行已取消",
            payload={},
        )
        await session.commit()
        return run


run_service = RunService()
