from __future__ import annotations

import json
import uuid

from app.services.llm_service import llm_service
from app.v2.core.errors import ConflictError
from app.v2.modules.capabilities.schemas import CapabilityGeneratePayload
from app.v2.modules.capabilities.service import capability_service
from app.v2.modules.env_profiles.service import env_profile_service
from app.v2.modules.tasks.repository import TaskRepositoryV2
from app.v2.modules.tasks.schemas import ClarificationAnswerPayload, TaskCreatePayload


class TaskServiceV2:
    def __init__(self) -> None:
        self.repository = TaskRepositoryV2()

    def _derive_title(self, payload: TaskCreatePayload) -> str:
        title = payload.title.strip()
        if title:
            return title
        first_line = payload.prompt.strip().splitlines()[0]
        return first_line[:48] if first_line else "未命名任务"

    def _fallback_requirement(self, prompt: str, answers: dict[str, str]) -> dict:
        missing_info: list[dict[str, str]] = []
        if len(prompt.strip()) < 18 and not answers:
            missing_info.append({"key": "deliverable", "question": "请补充希望交付的具体产品或文件。"})
        return {
            "goal": prompt.strip(),
            "scope": "围绕当前需求完成实现、验证和交付打包。",
            "inputs": {"prompt": prompt, "clarifications": answers},
            "outputs": {"primary_deliverable": self._derive_title(TaskCreatePayload(prompt=prompt, env_profile_id="", title="")), "report": "最终 Markdown 报告"},
            "constraints": {"must_review_and_test": True},
            "acceptance": {"definition": "主要流程可运行", "must_have": ["任务闭环", "结果可追溯"]},
            "missing_info": missing_info,
        }

    def _analyze_requirement(self, prompt: str, env_profile: dict, answers: dict[str, str]) -> dict:
        if env_profile.get("provider_type") != "openai_compatible":
            return self._fallback_requirement(prompt, answers)
        llm_result = llm_service.generate_text(
            (
                "你是任务需求分析器。返回严格 JSON，字段包含 goal, scope, outputs, acceptance, missing_info。\n"
                f"Prompt: {prompt}\nAnswers: {json.dumps(answers, ensure_ascii=False)}"
            ),
            env_profile,
            purpose="default",
        )
        try:
            parsed = json.loads(llm_result.get("content", "{}"))
        except json.JSONDecodeError:
            return self._fallback_requirement(prompt, answers)
        return {
            "goal": parsed.get("goal") or prompt.strip(),
            "scope": parsed.get("scope") or "围绕当前需求完成实现、验证和交付打包。",
            "inputs": {"prompt": prompt, "clarifications": answers},
            "outputs": parsed.get("outputs") or {"primary_deliverable": self._derive_title(TaskCreatePayload(prompt=prompt, env_profile_id="", title="")), "report": "最终 Markdown 报告"},
            "constraints": {"must_review_and_test": True, "model": llm_result.get("model", "")},
            "acceptance": parsed.get("acceptance") or {"definition": "主要流程可运行", "must_have": ["任务闭环"]},
            "missing_info": parsed.get("missing_info") or [],
        }

    def _decompose(self, prompt: str) -> tuple[list[dict], list[tuple[int, int]]]:
        lower = prompt.lower()
        subtasks: list[dict] = [
            {
                "id": str(uuid.uuid4()),
                "name": "实现后端执行链路",
                "description": "完成任务编排、能力绑定、执行证据与报告闭环。",
                "category": "backend",
                "priority": 10,
            }
        ]
        dependencies: list[tuple[int, int]] = []
        if any(token in lower for token in ("ui", "页面", "前端", "dashboard", "spa")):
            subtasks.append(
                {
                    "id": str(uuid.uuid4()),
                    "name": "实现前端工作台",
                    "description": "完成任务工作台、运行监控和环境配置视图。",
                    "category": "ui",
                    "priority": 20,
                }
            )
            dependencies.append((0, len(subtasks) - 1))
        subtasks.append(
            {
                "id": str(uuid.uuid4()),
                "name": "生成交付包与审计报告",
                "description": "输出 bundle、报告和审计索引。",
                "category": "documentation",
                "priority": 30,
            }
        )
        documentation_index = len(subtasks) - 1
        for index in range(documentation_index):
            dependencies.append((index, documentation_index))
        return subtasks, dependencies

    def _seed_capabilities(self, task: dict, run_id: str, item: dict) -> list[dict]:
        subtask_stub = {**item, "run_id": run_id}
        env_profile = env_profile_service.get_profile_for_runtime(task["env_profile_id"])
        agent = capability_service.generate_for_subtask("agent", task=task, subtask=subtask_stub, env_profile=env_profile)
        skill = capability_service.generate_for_subtask("skill", task=task, subtask=subtask_stub, env_profile=env_profile)
        return [
            {"capability_id": agent["id"], "version_id": agent["version_id"], "type": "agent"},
            {"capability_id": skill["id"], "version_id": skill["version_id"], "type": "skill"},
        ]

    def _materialize_after_requirement(self, task_id: str, task: dict, requirement: dict) -> dict:
        run = task["run"]
        subtasks = []
        raw_subtasks, dependencies = self._decompose(task["prompt"])
        for item in raw_subtasks:
            subtasks.append(
                {
                    **item,
                    "status": "PENDING",
                    "env_profile_id": task["env_profile_id"],
                    "capability_bindings": self._seed_capabilities(task, run["id"], {**item, "env_profile_id": task["env_profile_id"]}),
                    "acceptance": requirement["acceptance"],
                    "input_context": {"goal": requirement["goal"], "scope": requirement["scope"]},
                    "review_policy": {
                        "artifact_required": True,
                        "forbid_todo_markers": True,
                        "require_clean_exit": True,
                    },
                    "test_command": "python -c \"from pathlib import Path; import sys; sys.exit(0 if Path('result.txt').exists() else 1)\"",
                    "max_retries": 2,
                    "timeout_sec": 300,
                }
            )
        for from_index, to_index in dependencies:
            subtasks[to_index]["depends_on_ids"] = [
                *subtasks[to_index].get("depends_on_ids", []),
                subtasks[from_index]["id"],
            ]
        self.repository.replace_subtasks(task_id, run["id"], subtasks)
        self.repository.update_task_status(task_id, status="RUNNING", phase="WAITING_APPROVAL")
        self.repository.update_run_status(run["id"], status="WAITING_APPROVAL", phase="WAITING_APPROVAL")
        self.repository.append_event(
            task_id=task_id,
            run_id=run["id"],
            event_type="task.decomposed",
            message=f"Created {len(subtasks)} subtasks and candidate capabilities.",
            payload={"count": len(subtasks)},
        )
        return self.repository.get_task(task_id)

    def create_task(self, payload: TaskCreatePayload) -> dict:
        env_profile = env_profile_service.get_profile_for_runtime(payload.env_profile_id)
        task = self.repository.create_task(
            title=self._derive_title(payload),
            prompt=payload.prompt,
            env_profile_id=payload.env_profile_id,
            model_overrides=payload.model_overrides,
        )
        self.repository.append_event(
            task_id=task["id"],
            run_id=task["run"]["id"],
            event_type="task.created",
            message="Task created.",
        )
        requirement = self._analyze_requirement(
            payload.prompt,
            {
                "provider_type": env_profile.provider_type,
                "api_base_url": env_profile.api_base_url,
                "api_key": env_profile.api_key,
                "default_model": env_profile.default_model,
                "review_model": env_profile.review_model,
                "test_model": env_profile.test_model,
                "temperature": env_profile.temperature,
                "default_timeout_sec": env_profile.default_timeout_sec,
            },
            {},
        )
        self.repository.save_requirement(task["id"], requirement)
        if requirement["missing_info"]:
            self.repository.create_clarification_round(task["id"], requirement["missing_info"])
            self.repository.update_task_status(task["id"], status="WAITING_USER_INPUT", phase="WAITING_USER_INPUT")
            self.repository.update_run_status(task["run"]["id"], status="WAITING_USER_INPUT", phase="WAITING_USER_INPUT")
            self.repository.append_event(
                task_id=task["id"],
                run_id=task["run"]["id"],
                event_type="requirement.clarification.requested",
                message=f"{len(requirement['missing_info'])} clarification questions generated.",
                level="warn",
            )
            return self.repository.get_task(task["id"])
        return self._materialize_after_requirement(task["id"], task, requirement)

    def list_tasks(self) -> list[dict]:
        return self.repository.list_tasks()

    def get_task(self, task_id: str) -> dict:
        return self.repository.get_task(task_id)

    def answer_clarification(self, task_id: str, round_id: str, payload: ClarificationAnswerPayload) -> dict:
        task = self.repository.get_task(task_id)
        if task["status"] != "WAITING_USER_INPUT":
            raise ConflictError("Task is not waiting for clarification.")
        self.repository.answer_clarification_round(round_id, payload.answers)
        self.repository.append_event(
            task_id=task_id,
            run_id=task["run"]["id"],
            event_type="requirement.clarification.answered",
            message="Clarification answers submitted.",
        )
        env_profile = env_profile_service.get_profile_for_runtime(task["env_profile_id"])
        requirement = self._analyze_requirement(
            task["prompt"],
            {
                "provider_type": env_profile.provider_type,
                "api_base_url": env_profile.api_base_url,
                "api_key": env_profile.api_key,
                "default_model": env_profile.default_model,
                "review_model": env_profile.review_model,
                "test_model": env_profile.test_model,
                "temperature": env_profile.temperature,
                "default_timeout_sec": env_profile.default_timeout_sec,
            },
            payload.answers,
        )
        self.repository.save_requirement(task_id, requirement)
        return self._materialize_after_requirement(task_id, self.repository.get_task(task_id), requirement)


task_service_v2 = TaskServiceV2()
