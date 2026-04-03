from __future__ import annotations

from app.v2.core.models import CapabilitySpec
from app.v2.modules.capabilities.generator import build_agent_candidate, build_skill_candidate
from app.v2.modules.capabilities.repository import CapabilityRepository
from app.v2.modules.capabilities.schemas import CapabilityDecisionPayload, CapabilityGeneratePayload
from app.v2.modules.capabilities.state_machine import apply_approval_decision
from app.v2.modules.runtime.risk_scoring import score_capability_risk


class CapabilityService:
    def __init__(self) -> None:
        self.repository = CapabilityRepository()

    def _spec_from_payload(self, capability_type: str, payload: CapabilityGeneratePayload) -> CapabilitySpec:
        return CapabilitySpec(
            type=capability_type,
            name=payload.name,
            description=payload.description,
            instructions=payload.instructions,
            allowed_tools=payload.allowed_tools,
            allowed_commands=payload.allowed_commands,
            allowed_file_scope=payload.allowed_file_scope,
            risk_tags=payload.risk_tags,
            default_model_selector=payload.default_model_selector,
        )

    def generate(self, capability_type: str, payload: CapabilityGeneratePayload) -> dict:
        spec = self._spec_from_payload(capability_type, payload)
        risk_score = score_capability_risk(spec)
        rendered_spec = {
            "type": capability_type,
            "name": payload.name,
            "description": payload.description,
            "instructions": payload.instructions,
            "allowed_tools": payload.allowed_tools,
            "allowed_commands": payload.allowed_commands,
            "allowed_file_scope": payload.allowed_file_scope,
            "risk_tags": payload.risk_tags,
        }
        return self.repository.create_capability(
            capability_type=capability_type,
            name=payload.name,
            description=payload.description,
            rendered_spec=rendered_spec,
            risk_score=risk_score,
            source_task_id=payload.task_id,
            source_run_id=payload.run_id,
            default_model_selector=payload.default_model_selector,
            generation_model=getattr(payload, "generation_model", "") or payload.default_model_selector,
            generation_prompt=getattr(payload, "generation_prompt", "") or "",
            generation_raw_output=getattr(payload, "generation_raw_output", "") or payload.instructions,
            validation_summary={"risk_score": risk_score, "allowed_tools": payload.allowed_tools},
        )

    def generate_for_subtask(self, capability_type: str, *, task: dict, subtask: dict, env_profile) -> dict:
        candidate = build_agent_candidate(task, subtask, env_profile) if capability_type == "agent" else build_skill_candidate(task, subtask, env_profile)
        return self.generate(
            capability_type,
            CapabilityGeneratePayload(
                name=str(candidate["name"]),
                description=str(candidate["description"]),
                instructions=str(candidate["instructions"]),
                task_id=task["id"],
                run_id=subtask.get("run_id"),
                allowed_tools=list(candidate["allowed_tools"]),
                allowed_commands=list(candidate["allowed_commands"]),
                allowed_file_scope=list(candidate["allowed_file_scope"]),
                risk_tags=list(candidate["risk_tags"]),
                default_model_selector=str(candidate["default_model_selector"]),
                generation_model=str(candidate["generation_model"]),
                generation_prompt=str(candidate["generation_prompt"]),
                generation_raw_output=str(candidate["generation_raw_output"]),
            ),
        )

    def list_capabilities(self, capability_type: str | None = None, status: str | None = None) -> list[dict]:
        return self.repository.list_capabilities(capability_type=capability_type, status=status)

    def get_capability(self, capability_id: str) -> dict:
        return self.repository.get_capability(capability_id)

    def decide(self, capability_id: str, decision: str, payload: CapabilityDecisionPayload) -> dict:
        capability = self.repository.get_capability(capability_id)
        status = apply_approval_decision(capability["status"], decision)
        self.repository.update_version_status(capability["version_id"], status)
        self.repository.record_approval(capability["version_id"], decision, payload.approver, payload.comment)
        return self.repository.get_capability(capability_id)


capability_service = CapabilityService()
