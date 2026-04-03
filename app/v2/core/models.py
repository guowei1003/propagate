from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CapabilitySpec:
    type: str
    name: str
    description: str
    instructions: str
    allowed_tools: list[str]
    allowed_commands: list[str]
    allowed_file_scope: list[str]
    risk_tags: list[str]
    default_model_selector: str


@dataclass(slots=True)
class CapabilityVersion:
    capability_id: str
    version: int
    status: str
    content_hash: str
    rendered_spec: str
    risk_score: int
    source_task_id: str
    source_run_id: str
    default_model_selector: str = ""


@dataclass(slots=True)
class ExecutionEvidence:
    run_id: str
    sub_task_id: str
    command: str
    exit_code: int
    stdout_path: str
    stderr_path: str
    output_files: list[str]
    file_hashes: dict[str, str]
    container_metadata: dict[str, str]
    started_at: str
    completed_at: str


@dataclass(slots=True)
class BundleManifest:
    run_id: str
    task_id: str
    product_artifacts: list[str]
    agent_versions: list[dict[str, str | int]]
    skill_versions: list[dict[str, str | int]]
    evidence_indexes: list[dict[str, str | int]]
    report_indexes: list[str]
    checksums: dict[str, str]
    model_summary: dict[str, str] = field(default_factory=dict)
    env_profile_summary: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class EnvProfile:
    name: str
    provider_type: str
    api_base_url: str
    api_key: str
    default_model: str
    review_model: str
    test_model: str
    capability_generation_model: str
    report_model: str
    temperature: float
    default_timeout_sec: int
    max_retries: int
    max_concurrency: int
    enable_docker_sandbox: bool
    enable_auto_sub_agents: bool
