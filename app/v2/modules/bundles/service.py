from __future__ import annotations

import json
from pathlib import Path
import tarfile

from app.v2.core.config import v2_settings
from app.v2.modules.bundles.manifest import build_bundle_manifest
from app.v2.modules.capabilities.repository import CapabilityRepository
from app.v2.modules.tasks.repository import TaskRepositoryV2


class BundleService:
    def __init__(self) -> None:
        self.tasks = TaskRepositoryV2()
        self.capabilities = CapabilityRepository()

    def build_bundle(self, run_id: str) -> dict:
        run = self.tasks.get_run(run_id)
        task = self.tasks.get_task(run["task_id"])
        subtasks = self.tasks.list_run_subtasks(run_id)
        evidence_rows = self.tasks.list_execution_evidence(run_id)
        report = self.tasks.get_report(run_id)
        artifacts = self.tasks.list_artifacts(run_id)
        bundle_dir = v2_settings.bundle_root / run_id
        product_dir = bundle_dir / "product"
        agents_dir = bundle_dir / "agents"
        skills_dir = bundle_dir / "skills"
        logs_dir = bundle_dir / "logs"
        reports_dir = bundle_dir / "reports"
        for directory in (product_dir, agents_dir, skills_dir, logs_dir, reports_dir):
            directory.mkdir(parents=True, exist_ok=True)

        capability_versions = []
        model_summary = {}
        product_artifacts: list[str] = []
        for subtask in subtasks:
            summary = subtask.get("output_summary", {})
            if isinstance(summary, dict) and summary.get("selected_model"):
                model_summary[subtask["id"]] = summary["selected_model"]
            for binding in subtask["capability_bindings"]:
                capability = self.capabilities.get_capability(binding["capability_id"])
                capability_versions.append(capability)
                target_dir = skills_dir if binding["type"] == "skill" else agents_dir
                (target_dir / f"{capability['name']}.json").write_text(
                    json.dumps(capability["rendered_spec"], ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            workspace = v2_settings.runtime_root / run_id / subtask["id"]
            for item in workspace.rglob("*"):
                if not item.is_file():
                    continue
                rel = item.relative_to(workspace)
                if rel.name in {"stdout.log", "stderr.log", "execution-manifest.json"}:
                    continue
                target = product_dir / f"{subtask['id']}-{rel.name}"
                target.write_bytes(item.read_bytes())
                product_artifacts.append(f"product/{target.name}")

        for artifact in artifacts:
            target = logs_dir / Path(artifact["path"]).name.replace(":", "_")
            if Path(artifact["path"]).exists():
                target.write_bytes(Path(artifact["path"]).read_bytes())
        if report:
            report_path = reports_dir / "final-report.md"
            report_path.write_text(report["report_markdown"], encoding="utf-8")
        manifest = build_bundle_manifest(
            run_id=run_id,
            task_id=task["id"],
            product_artifacts=sorted(set(product_artifacts)),
            capability_versions=[
                type("Obj", (), {
                    "capability_id": item["id"],
                    "version": int(item["version"]),
                    "status": item["status"],
                    "content_hash": item["content_hash"],
                    "rendered_spec": json.dumps(item["rendered_spec"], ensure_ascii=False),
                    "risk_score": int(item["risk_score"]),
                    "source_task_id": item.get("source_task_id") or "",
                    "source_run_id": item.get("source_run_id") or "",
                    "default_model_selector": item.get("default_model_selector") or "",
                })()
                for item in capability_versions
            ],
            execution_evidence=[
                type("Obj", (), {
                    "sub_task_id": item["sub_task_id"],
                    "command": item["command"],
                    "exit_code": item["exit_code"],
                    "stdout_path": item["stdout_path"],
                    "stderr_path": item["stderr_path"],
                    "output_files": item["output_files"],
                    "file_hashes": item["file_hashes"],
                })()
                for item in evidence_rows
            ],
            reports=["reports/final-report.md"] if report else [],
            model_summary=model_summary,
            env_profile_summary={"env_profile_id": run["env_profile_id"]},
        )
        manifest_path = bundle_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
        self.tasks.save_artifact(task["id"], run_id, None, "bundle", str(manifest_path), "Bundle manifest", manifest.__dict__)
        return {"bundle_dir": str(bundle_dir), "manifest_path": str(manifest_path), "manifest": manifest.__dict__}

    def get_bundle(self, run_id: str) -> dict:
        manifest_path = v2_settings.bundle_root / run_id / "manifest.json"
        if manifest_path.exists():
            return {
                "bundle_dir": str(manifest_path.parent),
                "manifest_path": str(manifest_path),
                "manifest": json.loads(manifest_path.read_text(encoding="utf-8")),
            }
        return self.build_bundle(run_id)

    def get_bundle_archive(self, run_id: str) -> Path:
        bundle = self.get_bundle(run_id)
        bundle_dir = Path(bundle["bundle_dir"])
        archive_path = bundle_dir.parent / f"{run_id}.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(bundle_dir, arcname=run_id)
        return archive_path


bundle_service = BundleService()
