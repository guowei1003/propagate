from __future__ import annotations

from app.v2.core.models import CapabilityVersion, EnvProfile


def resolve_model_for_stage(
    stage: str,
    env_profile: EnvProfile,
    capability_version: CapabilityVersion | None,
    run_overrides: dict[str, str],
) -> str:
    override = (run_overrides or {}).get(stage, "").strip()
    if override:
        return override

    if stage == "execution" and capability_version and capability_version.default_model_selector.strip():
        return capability_version.default_model_selector.strip()

    mapping = {
        "capability_generation": env_profile.capability_generation_model,
        "review": env_profile.review_model,
        "test": env_profile.test_model,
        "report": env_profile.report_model,
        "requirement_analysis": env_profile.default_model,
        "task_decomposition": env_profile.default_model,
        "execution": env_profile.default_model,
    }
    selected = mapping.get(stage, "").strip()
    return selected or env_profile.default_model
