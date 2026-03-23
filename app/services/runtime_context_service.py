from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.config import settings
from app.repositories.common import utcnow


class RuntimeContextService:
    _SKILL_SNIPPETS: dict[str, str] = {
        "read_repo": "Inspect existing files and extract only relevant context before making changes.",
        "edit_file": "Apply minimal, reversible edits and keep behavior aligned with requirement acceptance.",
        "run_command": "Use deterministic commands and capture concise output summaries for traceability.",
        "generate_report": "Summarize outcomes, unresolved risks, and verification steps in markdown format.",
        "api_contract": "Define request/response contracts first and enforce compatibility constraints.",
        "design_system": "Keep interaction and visual styles consistent with product goals and audience.",
        "test_automation": "Create or run focused checks that directly validate stated acceptance criteria.",
        "deployment_pipeline": "Document build/release steps and environment assumptions before rollout.",
    }

    def _safe_filename(self, value: str) -> str:
        chars: list[str] = []
        for ch in value.strip().lower():
            if ch.isalnum() or ch in ("-", "_"):
                chars.append(ch)
            else:
                chars.append("-")
        collapsed = "".join(chars).strip("-")
        return collapsed or "skill"

    def _workspace_path(self, task_id: str, subtask_id: str) -> Path:
        return settings.artifacts_root / "sandboxes" / task_id / subtask_id

    def _write_skill_files(self, skill_dir: Path, skills: list[str], subtask_name: str, requirement_goal: str) -> list[str]:
        saved: list[str] = []
        for skill in skills:
            filename = f"{self._safe_filename(skill)}.md"
            content = [
                f"# Skill: {skill}",
                "",
                "## Objective",
                self._SKILL_SNIPPETS.get(skill, "Follow the task requirement and provide verifiable output."),
                "",
                "## Context",
                f"- Subtask: {subtask_name}",
                f"- Requirement Goal: {requirement_goal}",
                f"- Generated At: {utcnow()}",
            ]
            path = skill_dir / filename
            path.write_text("\n".join(content), encoding="utf-8")
            saved.append(str(path))
        return saved

    def prepare_subtask_runtime(
        self,
        *,
        task: dict,
        subtask_id: str,
        subtask_name: str,
        subtask_description: str,
        requirement: dict,
        agent_template: str,
        skills: list[str],
        timeout_sec: int,
        max_retries: int,
        env_profile: dict | None,
    ) -> dict:
        workspace = self._workspace_path(task["id"], subtask_id)
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        skills_dir = workspace / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        skill_files = self._write_skill_files(
            skill_dir=skills_dir,
            skills=skills,
            subtask_name=subtask_name,
            requirement_goal=requirement.get("goal", ""),
        )

        runtime_manifest = {
            "task_id": task["id"],
            "subtask_id": subtask_id,
            "subtask_name": subtask_name,
            "subtask_description": subtask_description,
            "agent_name": agent_template,
            "skills": skills,
            "timeout_sec": timeout_sec,
            "max_retries": max_retries,
            "sandbox_mode": "docker" if bool(int((env_profile or {}).get("enable_docker_sandbox") or 0)) else "workspace",
            "requirement_goal": requirement.get("goal", ""),
            "created_at": utcnow(),
        }
        manifest_path = workspace / "agent-manifest.json"
        manifest_path.write_text(json.dumps(runtime_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        requirement_path = workspace / "requirement-snapshot.md"
        requirement_path.write_text(
            "\n".join(
                [
                    "# Requirement Snapshot",
                    "",
                    f"Goal: {requirement.get('goal', '')}",
                    "",
                    f"Scope: {requirement.get('scope', '')}",
                ]
            ),
            encoding="utf-8",
        )

        return {
            "workspace_path": str(workspace),
            "skills_dir": str(skills_dir),
            "skill_files": skill_files,
            "manifest_path": str(manifest_path),
            "sandbox_mode": runtime_manifest["sandbox_mode"],
            "agent_name": agent_template,
        }


runtime_context_service = RuntimeContextService()
