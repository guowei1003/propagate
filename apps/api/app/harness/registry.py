from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from app.config import ROOT_DIR
from app.harness.contracts import AgentSpec


REGISTRY_DIR = ROOT_DIR / "agents" / "registry"


@lru_cache
def load_registry() -> dict[str, AgentSpec]:
    registry: dict[str, AgentSpec] = {}
    for path in sorted(REGISTRY_DIR.glob("*.yaml")):
        payload = yaml.safe_load(path.read_text())
        spec = AgentSpec.model_validate(payload)
        registry[spec.id] = spec
    return registry


def list_agents() -> list[AgentSpec]:
    return list(load_registry().values())


def get_agent(agent_id: str) -> AgentSpec:
    registry = load_registry()
    if agent_id not in registry:
        raise KeyError(f"Unknown agent: {agent_id}")
    return registry[agent_id]
