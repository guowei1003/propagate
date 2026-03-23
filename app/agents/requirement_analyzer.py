from __future__ import annotations

from app.domain.models import RequirementAnalysis
from app.services.llm_service import llm_service


class RequirementAnalyzerAgent:
    _QUESTION_BANK: dict[str, str] = {
        "deliverable": "希望最终交付什么结果？例如代码改动、设计文档、接口实现或测试报告。",
        "acceptance": "请给出验收标准，例如页面可访问、接口可调用、测试通过、报告生成。",
        "scope": "任务范围还不够清晰，请补充涉及的模块、页面或接口范围。",
        "target_users": "目标用户是谁？请描述主要用户画像和使用场景。",
        "core_features": "请列出 3-5 个核心功能，按优先级从高到低描述。",
        "style_preferences": "是否有 UI/交互风格偏好？例如极简、营销型、B 端控制台风格。",
        "platforms": "APP 需要支持哪些平台？例如 iOS、Android、Web。",
        "integration_constraints": "是否需要对接第三方服务或既有系统？请列出关键接口约束。",
    }

    def _normalize_answers(self, answers: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for key, value in answers.items():
            text = str(value).strip()
            if text:
                normalized[key] = text
        return normalized

    def _detect_project_type(self, prompt: str) -> str:
        lower = prompt.lower()
        if any(token in lower for token in ["app", "ios", "android", "客户端"]):
            return "app"
        if any(token in lower for token in ["website", "web", "网站", "官网", "landing page"]):
            return "website"
        return "generic"

    def _required_keys(self, prompt: str, project_type: str) -> list[str]:
        required = ["deliverable", "acceptance"]
        if len(prompt.strip()) < 24:
            required.append("scope")
        if project_type in {"website", "app"}:
            required.extend(["target_users", "core_features", "style_preferences"])
        if project_type == "app":
            required.append("platforms")
        if any(token in prompt.lower() for token in ["集成", "integration", "支付", "登录", "第三方"]):
            required.append("integration_constraints")
        return required

    def run(self, prompt: str, answers: dict[str, str], env_profile: dict | None = None) -> RequirementAnalysis:
        normalized_answers = self._normalize_answers(answers)
        deliverable = normalized_answers.get("deliverable", "")
        acceptance = normalized_answers.get("acceptance", "")
        scope_hint = normalized_answers.get("scope", "")
        project_type = self._detect_project_type(prompt)
        llm_hint = llm_service.generate_json(
            f"Analyze requirement prompt and identify missing information.\nPrompt: {prompt}\nAnswers: {answers}",
            "requirement_analysis",
            env_profile,
            purpose="default",
        )

        missing_info: list[dict[str, str]] = []
        for key in self._required_keys(prompt, project_type):
            if normalized_answers.get(key):
                continue
            missing_info.append({"key": key, "question": self._QUESTION_BANK[key]})

        goal = prompt.strip()
        scope = scope_hint or "围绕当前提示词所述目标进行实现、验证和报告输出。"
        inputs = {"prompt": prompt, "clarifications": normalized_answers}
        outputs = {
            "primary_deliverable": deliverable or "待澄清",
            "report": "最终 Markdown 报告",
            "project_type": project_type,
        }
        constraints = {
            "control_mode": "orchestrated",
            "must_review_and_test": True,
            "minimize_dependencies": True,
            "model_provider": llm_hint["provider_type"],
            "model_name": llm_hint["model"],
            "enable_auto_sub_agents": bool(int((env_profile or {}).get("enable_auto_sub_agents") or 0)),
            "enable_docker_sandbox": bool(int((env_profile or {}).get("enable_docker_sandbox") or 0)),
        }
        acceptance_payload = {
            "definition": acceptance or "待澄清",
            "must_have": [
                "需求解析完成",
                "子任务拆解完成",
                "子任务经过 review 与 test",
                "最终报告生成",
            ],
        }
        if project_type in {"website", "app"}:
            acceptance_payload["must_have"].append("用户核心流程可演示")
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
