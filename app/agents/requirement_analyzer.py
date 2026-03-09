from __future__ import annotations

from app.domain.models import RequirementAnalysis
from app.services.llm_service import llm_service


class RequirementAnalyzerAgent:
    def run(self, prompt: str, answers: dict[str, str], env_profile: dict | None = None) -> RequirementAnalysis:
        deliverable = answers.get("deliverable", "").strip()
        acceptance = answers.get("acceptance", "").strip()
        scope_hint = answers.get("scope", "").strip()
        llm_hint = llm_service.generate_json(
            f"Analyze requirement prompt and identify missing information.\nPrompt: {prompt}\nAnswers: {answers}",
            "requirement_analysis",
            env_profile,
            purpose="default",
        )

        missing_info: list[dict[str, str]] = []
        if not deliverable:
            missing_info.append(
                {
                    "key": "deliverable",
                    "question": "希望最终交付什么结果？例如代码改动、设计文档、接口实现或测试报告。",
                }
            )
        if not acceptance:
            missing_info.append(
                {
                    "key": "acceptance",
                    "question": "请给出验收标准，例如页面可访问、接口可调用、测试通过、报告生成。",
                }
            )
        if len(prompt.strip()) < 24 and not scope_hint:
            missing_info.append(
                {
                    "key": "scope",
                    "question": "任务范围还不够清晰，请补充涉及的模块、页面或接口范围。",
                }
            )

        goal = prompt.strip()
        scope = scope_hint or "围绕当前提示词所述目标进行实现、验证和报告输出。"
        inputs = {"prompt": prompt, "clarifications": answers}
        outputs = {
            "primary_deliverable": deliverable or "待澄清",
            "report": "最终 Markdown 报告",
        }
        constraints = {
            "control_mode": "orchestrated",
            "must_review_and_test": True,
            "minimize_dependencies": True,
            "model_provider": llm_hint["provider_type"],
            "model_name": llm_hint["model"],
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
