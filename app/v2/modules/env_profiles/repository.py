from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.v2.core.db import dumps_json, execute, fetch_all, fetch_one
from app.v2.core.errors import ConflictError, NotFoundError
from app.v2.modules.env_profiles.schemas import EnvProfileCreatePayload, EnvProfileUpdatePayload


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _is_unique_violation(exc: Exception) -> bool:
    if getattr(exc, "sqlstate", None) == "23505":
        return True
    if getattr(exc, "pgcode", None) == "23505":
        return True
    if "uniqueviolation" in exc.__class__.__name__.lower():
        return True
    lowered = str(exc).lower()
    return "duplicate key value violates unique constraint" in lowered


def _is_missing_relation_or_column(exc: Exception) -> bool:
    sqlstate = getattr(exc, "sqlstate", None) or getattr(exc, "pgcode", None)
    if sqlstate in {"42P01", "42703"}:
        return True
    class_name = exc.__class__.__name__.lower()
    if "undefinedtable" in class_name or "undefinedcolumn" in class_name:
        return True
    lowered = str(exc).lower()
    return "does not exist" in lowered and (
        "env_profiles" in lowered or "provider_type" in lowered or "api_base_url" in lowered
    )


class EnvProfileRepository:
    def list_profiles(self) -> list[dict[str, Any]]:
        try:
            return fetch_all("SELECT * FROM env_profiles ORDER BY created_at ASC")
        except Exception as exc:
            if _is_missing_relation_or_column(exc):
                raise NotFoundError(
                    "未检测到可用环境配置，请先新增环境配置。",
                    code="ENV_PROFILE_NOT_CONFIGURED",
                ) from exc
            raise

    def get_profile(self, profile_id: str) -> dict[str, Any]:
        row = fetch_one("SELECT * FROM env_profiles WHERE id = %s", (profile_id,))
        if not row:
            raise NotFoundError(f"Env profile {profile_id} not found.")
        return row

    def get_profile_for_runtime(self, profile_id: str) -> dict[str, Any]:
        return self.get_profile(profile_id)

    def create_profile(self, payload: EnvProfileCreatePayload) -> dict[str, Any]:
        profile_id = str(uuid.uuid4())
        now = utcnow()
        try:
            execute(
                """
                INSERT INTO env_profiles (
                    id, name, provider_type, api_base_url, api_key, default_model, review_model,
                    test_model, capability_generation_model, report_model, temperature,
                    default_timeout_sec, max_retries, max_concurrency, enable_docker_sandbox,
                    enable_auto_sub_agents, metadata_json, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    profile_id,
                    payload.name,
                    payload.provider_type,
                    payload.api_base_url,
                    payload.api_key,
                    payload.default_model,
                    payload.review_model,
                    payload.test_model,
                    payload.capability_generation_model,
                    payload.report_model,
                    payload.temperature,
                    payload.default_timeout_sec,
                    payload.max_retries,
                    payload.max_concurrency,
                    payload.enable_docker_sandbox,
                    payload.enable_auto_sub_agents,
                    dumps_json({}),
                    now,
                    now,
                ),
            )
        except Exception as exc:
            if _is_unique_violation(exc):
                raise ConflictError(
                    "环境配置名称已存在，请更换后重试。",
                    code="ENV_PROFILE_NAME_CONFLICT",
                ) from exc
            raise
        return self.get_profile(profile_id)

    def update_profile(self, profile_id: str, payload: EnvProfileUpdatePayload) -> dict[str, Any]:
        now = utcnow()
        try:
            execute(
                """
                UPDATE env_profiles
                SET
                    name = %s,
                    provider_type = %s,
                    api_base_url = %s,
                    api_key = %s,
                    default_model = %s,
                    review_model = %s,
                    test_model = %s,
                    capability_generation_model = %s,
                    report_model = %s,
                    temperature = %s,
                    default_timeout_sec = %s,
                    max_retries = %s,
                    max_concurrency = %s,
                    enable_docker_sandbox = %s,
                    enable_auto_sub_agents = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (
                    payload.name,
                    payload.provider_type,
                    payload.api_base_url,
                    payload.api_key,
                    payload.default_model,
                    payload.review_model,
                    payload.test_model,
                    payload.capability_generation_model,
                    payload.report_model,
                    payload.temperature,
                    payload.default_timeout_sec,
                    payload.max_retries,
                    payload.max_concurrency,
                    payload.enable_docker_sandbox,
                    payload.enable_auto_sub_agents,
                    now,
                    profile_id,
                ),
            )
        except Exception as exc:
            if _is_unique_violation(exc):
                raise ConflictError(
                    "环境配置名称已存在，请更换后重试。",
                    code="ENV_PROFILE_NAME_CONFLICT",
                ) from exc
            raise
        return self.get_profile(profile_id)
