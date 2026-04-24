from __future__ import annotations

from fastapi import APIRouter

from app.harness.registry import list_agents
from app.schemas.agents import AgentSpecResponse


router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentSpecResponse])
async def get_agents():
    return [AgentSpecResponse.model_validate(agent.model_dump()) for agent in list_agents()]
