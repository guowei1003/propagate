from __future__ import annotations

import json

from app.services.llm_service import llm_service
from app.v2.core.models import EnvProfile
from app.v2.modules.env_profiles.model_routing import resolve_model_for_stage


def _runtime_env(profile: EnvProfile, model: str) -> dict[str, str | float | int]:
    return {
        "provider_type": profile.provider_type,
        "api_base_url": profile.api_base_url,
        "api_key": profile.api_key,
        "default_model": model,
        "review_model": profile.review_model or model,
        "test_model": profile.test_model or model,
        "temperature": profile.temperature,
        "default_timeout_sec": profile.default_timeout_sec,
    }


def _default_agent_payload(task: dict, subtask: dict, model: str) -> dict[str, object]:
    raw_category = str(subtask.get("category") or "generic")
    category = "frontend" if raw_category == "ui" else raw_category
    return {
        "name": f"{category}-agent",
        "description": f"{subtask['name']} agent",
        "instructions": (
            f"围绕任务《{task['title']}》执行子任务《{subtask['name']}》，"
            f"重点满足：{subtask.get('description', '')}"
        ),
        "allowed_tools": ["read_repo", "run_command"],
        "allowed_commands": [],
        "allowed_file_scope": ["/workspace"],
        "risk_tags": [category],
        "default_model_selector": model,
    }


def _default_skill_payload(task: dict, subtask: dict, model: str) -> dict[str, object]:
    raw_category = str(subtask.get("category") or "generic")
    category = "frontend" if raw_category == "ui" else raw_category
    command = "printf 'subtask executed\\n' > result.txt"
    if raw_category == "backend":
        command = "printf 'backend task complete\\n' > result.txt"
    elif raw_category == "ui":
        command = "printf 'ui task complete\\n' > result.txt"
    return {
        "name": f"{category}-skill",
        "description": f"{subtask['name']} skill",
        "instructions": f"为《{subtask['name']}》提供可审计的执行能力。",
        "allowed_tools": ["run_command"],
        "allowed_commands": [command],
        "allowed_file_scope": ["/workspace"],
        "risk_tags": [category],
        "default_model_selector": model,
    }


def _try_generate_with_llm(task: dict, subtask: dict, profile: EnvProfile, default_payload: dict[str, object], capability_type: str) -> tuple[dict[str, object], str, str]:
    selected_model = resolve_model_for_stage("capability_generation", profile, None, {})
    if profile.provider_type != "openai_compatible":
        return default_payload, selected_model, json.dumps(default_payload, ensure_ascii=False)
    prompt = (
        "你是能力工厂生成器。输出严格 JSON，字段包含 "
        "name, description, instructions, allowed_tools, allowed_commands, allowed_file_scope, risk_tags, default_model_selector。\n"
        f"Task: {task['title']}\n"
        f"Subtask: {subtask['name']}\n"
        f"SubtaskDescription: {subtask.get('description', '')}\n"
        f"CapabilityType: {capability_type}\n"
    )
    llm_result = llm_service.generate_text(
        prompt,
        _runtime_env(profile, selected_model),
        purpose="default",
        system_prompt="Return valid JSON only.",
    )
    raw = llm_result.get("content", "")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return default_payload, llm_result.get("model", selected_model), raw
    merged = {**default_payload, **parsed}
    merged["allowed_file_scope"] = merged.get("allowed_file_scope") or ["/workspace"]
    merged["default_model_selector"] = merged.get("default_model_selector") or selected_model
    return merged, llm_result.get("model", selected_model), raw


def build_agent_candidate(task: dict, subtask: dict, profile: EnvProfile) -> dict[str, object]:
    default_payload = _default_agent_payload(task, subtask, resolve_model_for_stage("capability_generation", profile, None, {}))
    generated, generation_model, raw_output = _try_generate_with_llm(task, subtask, profile, default_payload, "agent")
    generated["generation_model"] = generation_model
    generated["generation_prompt"] = f"{task['title']}::{subtask['name']}::agent"
    generated["generation_raw_output"] = raw_output
    return generated


def build_skill_candidate(task: dict, subtask: dict, profile: EnvProfile) -> dict[str, object]:
    default_payload = _default_skill_payload(task, subtask, resolve_model_for_stage("capability_generation", profile, None, {}))
    generated, generation_model, raw_output = _try_generate_with_llm(task, subtask, profile, default_payload, "skill")
    generated["generation_model"] = generation_model
    generated["generation_prompt"] = f"{task['title']}::{subtask['name']}::skill"
    generated["generation_raw_output"] = raw_output
    return generated
