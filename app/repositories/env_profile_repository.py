from __future__ import annotations

import uuid

from app.config import settings
from app.db import transaction
from app.repositories.common import row_to_dict, utcnow


class EnvProfileRepository:
    def _sanitize(self, payload: dict) -> dict:
        if not payload:
            return payload
        sanitized = dict(payload)
        api_key = sanitized.pop("api_key", None)
        sanitized["has_api_key"] = bool(api_key)
        sanitized["api_key_masked"] = self._mask_secret(api_key)
        return sanitized

    def _mask_secret(self, value: str | None) -> str:
        if not value:
            return ""
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:4]}...{value[-4:]}"

    def list_profiles(self) -> list[dict]:
        with transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM env_profiles ORDER BY created_at ASC"
            ).fetchall()
        return [self._sanitize(row_to_dict(row)) for row in rows]

    def get_profile(self, profile_id: str) -> dict | None:
        with transaction() as conn:
            row = conn.execute(
                "SELECT * FROM env_profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()
        return self._sanitize(row_to_dict(row)) if row else None

    def get_profile_for_runtime(self, profile_id: str) -> dict | None:
        with transaction() as conn:
            row = conn.execute(
                "SELECT * FROM env_profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()
        return row_to_dict(row) if row else None

    def get_default_profile(self) -> dict | None:
        with transaction() as conn:
            row = conn.execute(
                "SELECT * FROM env_profiles ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
        return self._sanitize(row_to_dict(row)) if row else None

    def get_default_profile_for_runtime(self) -> dict | None:
        with transaction() as conn:
            row = conn.execute(
                "SELECT * FROM env_profiles ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
        return row_to_dict(row) if row else None

    def create_profile(
        self,
        name: str,
        provider_type: str,
        api_base_url: str,
        api_key: str,
        default_model: str,
        review_model: str,
        test_model: str,
        temperature: float,
        max_concurrency: int,
        default_timeout_sec: int,
        max_retries: int,
        enable_auto_sub_agents: bool,
        enable_docker_sandbox: bool,
    ) -> str:
        profile_id = str(uuid.uuid4())
        now = utcnow()
        with transaction() as conn:
            conn.execute(
                """
                INSERT INTO env_profiles (
                    id, name, provider_type, api_base_url, api_key,
                    default_model, review_model, test_model, temperature,
                    max_concurrency, default_timeout_sec, max_retries,
                    enable_auto_sub_agents, enable_docker_sandbox,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_id,
                    name,
                    provider_type,
                    api_base_url or None,
                    api_key or None,
                    default_model,
                    review_model,
                    test_model,
                    temperature,
                    max_concurrency,
                    default_timeout_sec,
                    max_retries,
                    int(enable_auto_sub_agents),
                    int(enable_docker_sandbox),
                    now,
                    now,
                ),
            )
        return profile_id

    def seed_default_profile(self) -> None:
        """Create default profile from environment variables or demo mode."""
        if self.get_default_profile():
            return
        # Use environment variables if configured
        llm_config = settings.llm
        if llm_config.provider_type != "demo" and llm_config.api_base_url and llm_config.api_key:
            self.create_profile(
                name="Default (from env)",
                provider_type=llm_config.provider_type,
                api_base_url=llm_config.api_base_url,
                api_key=llm_config.api_key,
                default_model=llm_config.default_model,
                review_model=llm_config.review_model or llm_config.default_model,
                test_model=llm_config.test_model or llm_config.default_model,
                temperature=llm_config.temperature,
                max_concurrency=2,
                default_timeout_sec=llm_config.timeout_sec,
                max_retries=llm_config.max_retries,
                enable_auto_sub_agents=True,
                enable_docker_sandbox=False,
            )
        else:
            # Fallback to demo mode
            self.create_profile(
                name="Default",
                provider_type="demo",
                api_base_url="",
                api_key="",
                default_model="demo-heuristic",
                review_model="demo-review",
                test_model="demo-test",
                temperature=0.2,
                max_concurrency=2,
                default_timeout_sec=300,
                max_retries=2,
                enable_auto_sub_agents=True,
                enable_docker_sandbox=False,
            )
