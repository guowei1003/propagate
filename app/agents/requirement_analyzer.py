from __future__ import annotations

import json
import re
from typing import Any

from app.domain.models import RequirementAnalysis
from app.services.llm_service import llm_service


class RequirementAnalyzerAgent:
    def _build_analysis_prompt(self, prompt: str, answers: dict[str, str]) -> str:
        answer_block = json.dumps(answers, ensure_ascii=False, indent=2)
        return (
            "你是需求澄清助手。请基于用户初始需求与已有澄清回答，返回严格 JSON，不要输出任何额外文字。\n"
            "要求：\n"
            "1) JSON 顶层字段必须包含 goal, scope, outputs, acceptance, missing_info。\n"
            "2) missing_info 必须是数组，元素为对象，字段仅包含 key 与 question。\n"
            "3) key 使用简短 snake_case，便于表单提交。\n"
            "4) 只保留仍然缺失、会影响实施的问题；不要重复已回答信息。\n"
            "5) 如果信息已足够，则 missing_info 返回空数组。\n"
            "6) 每轮最多返回 8 个问题，按优先级排序。\n\n"
            f"初始需求:\n{prompt}\n\n"
            f"已回答澄清:\n{answer_block}\n\n"
            "输出示例（仅结构示例，不可照抄值）:\n"
            '{"goal":"...","scope":"...","outputs":{"primary_deliverable":"...","report":"最终 Markdown 报告"},"acceptance":{"definition":"...","must_have":["..."]},"missing_info":[{"key":"...","question":"..."}]}'
        )

    def _parse_analysis_content(self, raw: str) -> dict[str, Any]:
        text = (raw or "").strip()
        if not text:
            raise ValueError("LLM returned empty requirement analysis content.")
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
        candidate = fenced.group(1).strip() if fenced else text
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM requirement analysis is not valid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("LLM requirement analysis payload must be a JSON object.")
        return payload

    def _normalize_answers(self, answers: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for key, value in answers.items():
            cleaned_key = str(key).strip()
            text = str(value).strip()
            if cleaned_key and text:
                normalized[cleaned_key] = text
        return normalized

    def _normalize_missing_info(self, items: Any) -> list[dict[str, str]]:
        if not isinstance(items, list):
            return []
        normalized: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key", "")).strip().lower().replace(" ", "_")
            question = str(item.get("question", "")).strip()
            if not key or not question or key in seen:
                continue
            seen.add(key)
            normalized.append({"key": key, "question": question})
            if len(normalized) >= 8:
                break
        return normalized

    def run(self, prompt: str, answers: dict[str, str], env_profile: dict | None = None) -> RequirementAnalysis:
        provider_type = (env_profile or {}).get("provider_type")
        if provider_type != "openai_compatible":
            raise ValueError("Requirement clarification requires openai_compatible provider.")
        normalized_answers = self._normalize_answers(answers)
        llm_result = llm_service.generate_text(
            self._build_analysis_prompt(prompt, normalized_answers),
            env_profile,
            purpose="default",
        )
        parsed = self._parse_analysis_content(llm_result.get("content", ""))
        missing_info = self._normalize_missing_info(parsed.get("missing_info", []))
        goal = str(parsed.get("goal") or prompt).strip()
        scope = str(parsed.get("scope") or "围绕当前提示词所述目标进行实现、验证和报告输出。").strip()
        inputs = {"prompt": prompt, "clarifications": normalized_answers}
        outputs_payload = parsed.get("outputs") if isinstance(parsed.get("outputs"), dict) else {}
        acceptance_payload = parsed.get("acceptance") if isinstance(parsed.get("acceptance"), dict) else {}
        outputs = {
            "primary_deliverable": outputs_payload.get("primary_deliverable", "待澄清"),
            "report": outputs_payload.get("report", "最终 Markdown 报告"),
            **outputs_payload,
        }
        constraints = {
            "control_mode": "orchestrated",
            "must_review_and_test": True,
            "minimize_dependencies": True,
            "model_provider": llm_result.get("provider_type", "unknown"),
            "model_name": llm_result.get("model", "unknown"),
            "enable_auto_sub_agents": bool(int((env_profile or {}).get("enable_auto_sub_agents") or 0)),
            "enable_docker_sandbox": bool(int((env_profile or {}).get("enable_docker_sandbox") or 0)),
        }
        must_have = acceptance_payload.get("must_have")
        if not isinstance(must_have, list):
            must_have = []
        acceptance_payload = {
            "definition": acceptance_payload.get("definition", "待澄清"),
            "must_have": [str(item).strip() for item in must_have if str(item).strip()],
            **acceptance_payload,
        }
        return RequirementAnalysis(
            goal=goal,
            scope=scope,
            inputs=inputs,
            outputs=outputs,
            constraints=constraints,
            acceptance=acceptance_payload,
            missing_info=missing_info,
        )


requirement_analyzer_agent = RequirementAnalyzerAgent()
