from __future__ import annotations

from copy import deepcopy


DEFAULT_MEMORY = {
    "mission": None,
    "facts": [],
    "assumptions": [],
    "decisions": [],
    "current_plan": None,
    "completed_steps": [],
    "open_issues": [],
    "artifacts": [],
}


def create_memory() -> dict:
    return deepcopy(DEFAULT_MEMORY)


def remember(memory: dict, section: str, value) -> dict:
    updated = deepcopy(memory)
    if section not in updated:
        updated[section] = []
    if isinstance(updated[section], list):
        updated[section].append(value)
    else:
        updated[section] = value
    return updated
