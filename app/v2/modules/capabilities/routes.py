from __future__ import annotations

from fastapi import APIRouter

from app.v2.modules.capabilities.schemas import CapabilityDecisionPayload, CapabilityGeneratePayload
from app.v2.modules.capabilities.service import capability_service


router = APIRouter(prefix="/v2/capabilities", tags=["v2-capabilities"])


@router.get("")
def list_capabilities(type: str | None = None, status: str | None = None):
    return capability_service.list_capabilities(capability_type=type, status=status)


@router.get("/{capability_id}")
def get_capability(capability_id: str):
    return capability_service.get_capability(capability_id)


@router.post("/agents/generate")
def generate_agent(payload: CapabilityGeneratePayload):
    return capability_service.generate("agent", payload)


@router.post("/skills/generate")
def generate_skill(payload: CapabilityGeneratePayload):
    return capability_service.generate("skill", payload)


@router.post("/{capability_id}/approve")
def approve_capability(capability_id: str, payload: CapabilityDecisionPayload):
    return capability_service.decide(capability_id, "approve", payload)


@router.post("/{capability_id}/reject")
def reject_capability(capability_id: str, payload: CapabilityDecisionPayload):
    return capability_service.decide(capability_id, "reject", payload)
