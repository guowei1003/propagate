from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from app.config import settings


class LLMService:
    """
    Supports a local demo mode and an OpenAI-compatible mode driven entirely
    by the selected environment profile.
    """

    def resolve_model(self, env_profile: dict | None, purpose: str) -> str:
        if not env_profile:
            return settings.default_model
        if purpose == "review":
            return env_profile.get("review_model") or env_profile.get("default_model") or settings.default_model
        if purpose == "test":
            return env_profile.get("test_model") or env_profile.get("default_model") or settings.default_model
        return env_profile.get("default_model") or settings.default_model

    def generate_json(
        self,
        prompt: str,
        schema_name: str,
        env_profile: dict | None,
        *,
        purpose: str = "default",
    ) -> dict[str, Any]:
        chosen_model = self.resolve_model(env_profile, purpose)
        provider_type = (env_profile or {}).get("provider_type") or "demo"
        if provider_type == "openai_compatible":
            text_result = self.generate_text(
                prompt,
                env_profile,
                purpose=purpose,
                system_prompt=f"Return a concise answer that fits schema: {schema_name}.",
            )
            return {
                "model": text_result["model"],
                "provider_type": provider_type,
                "schema": schema_name,
                "content": text_result["content"],
            }
        return {
            "model": chosen_model,
            "provider_type": provider_type,
            "schema": schema_name,
            "prompt_length": len(prompt),
        }

    def generate_text(
        self,
        prompt: str,
        env_profile: dict | None,
        *,
        purpose: str = "default",
        system_prompt: str = "You are a precise software delivery assistant.",
    ) -> dict[str, Any]:
        provider_type = (env_profile or {}).get("provider_type") or "demo"
        model = self.resolve_model(env_profile, purpose)
        if provider_type != "openai_compatible":
            return {
                "provider_type": "demo",
                "model": model,
                "content": f"[demo:{model}] {prompt[:180]}",
            }
        try:
            return self._call_openai_compatible(
                prompt=prompt,
                system_prompt=system_prompt,
                env_profile=env_profile or {},
                model=model,
            )
        except Exception as exc:
            return {
                "provider_type": "openai_compatible",
                "model": model,
                "content": f"[llm-error] {exc}",
                "error": str(exc),
            }

    def _call_openai_compatible(
        self,
        *,
        prompt: str,
        system_prompt: str,
        env_profile: dict,
        model: str,
    ) -> dict[str, Any]:
        api_base_url = (env_profile.get("api_base_url") or "").strip()
        api_key = (env_profile.get("api_key") or "").strip()
        if not api_base_url:
            raise ValueError("OpenAI compatible mode requires api_base_url.")
        if not api_key:
            raise ValueError("OpenAI compatible mode requires api_key.")
        endpoint = api_base_url.rstrip("/")
        if not endpoint.endswith("/chat/completions"):
            endpoint = f"{endpoint}/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": float(env_profile.get("temperature") or 0.2),
        }
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with request.urlopen(
                req,
                timeout=int(env_profile.get("default_timeout_sec") or settings.default_timeout_sec),
            ) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM HTTP error {exc.code}: {body}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"LLM connection failed: {exc.reason}") from exc
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        return {
            "provider_type": "openai_compatible",
            "model": data.get("model", model),
            "content": content,
            "raw": data,
        }


llm_service = LLMService()
