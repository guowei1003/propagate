from __future__ import annotations

from app.services.llm_service import llm_service


class ReportAgent:
    def run(self, task: dict, requirement: dict, subtasks: list[dict], events: list[dict], env_profile: dict | None = None) -> tuple[str, dict]:
        completed = [item for item in subtasks if item["status"] == "COMPLETED"]
        blocked = [item for item in subtasks if item["status"] == "NEEDS_HUMAN_REVIEW"]
        model_output = llm_service.generate_text(
            f"Summarize task completion.\nTask: {task['title']}\nSubtasks: {[(item['name'], item['status']) for item in subtasks]}",
            env_profile,
            purpose="default",
            system_prompt="You are a reporting assistant. Return a concise executive summary.",
        )
        lines = [
            f"# Task Report: {task['title']}",
            "",
            "## Summary",
            f"- Status: {task['status']}",
            f"- Phase: {task['current_phase']}",
            f"- Progress: {task['progress_percent']}%",
            f"- Model: {model_output['provider_type']} / {model_output['model']}",
            "",
            "## Requirement",
            requirement["goal"],
            "",
            "## Executive Summary",
            model_output["content"],
            "",
            "## Subtasks",
        ]
        for item in subtasks:
            lines.append(f"- {item['name']}: {item['status']}")
        lines.extend(["", "## Event Count", f"{len(events)} events captured."])
        summary = {
            "completed_subtasks": len(completed),
            "blocked_subtasks": len(blocked),
            "event_count": len(events),
            "provider_type": model_output["provider_type"],
            "model": model_output["model"],
        }
        return "\n".join(lines), summary


report_agent = ReportAgent()
