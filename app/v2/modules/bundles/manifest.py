from __future__ import annotations

from app.v2.core.models import BundleManifest, CapabilityVersion, ExecutionEvidence


def build_bundle_manifest(
    *,
    run_id: str,
    task_id: str,
    product_artifacts: list[str],
    capability_versions: list[CapabilityVersion],
    execution_evidence: list[ExecutionEvidence],
    reports: list[str],
    model_summary: dict[str, str],
    env_profile_summary: dict[str, str],
) -> BundleManifest:
    checksums: dict[str, str] = {}
    agent_versions: list[dict[str, str | int]] = []
    skill_versions: list[dict[str, str | int]] = []
    evidence_indexes: list[dict[str, str | int]] = []

    for version in capability_versions:
        item = {
            "capability_id": version.capability_id,
            "version": version.version,
            "content_hash": version.content_hash,
            "model_selector": version.default_model_selector,
        }
        if "skill" in version.capability_id:
            skill_versions.append(item)
        else:
            agent_versions.append(item)

    for evidence in execution_evidence:
        checksums.update(evidence.file_hashes)
        evidence_indexes.append(
            {
                "sub_task_id": evidence.sub_task_id,
                "command": evidence.command,
                "exit_code": evidence.exit_code,
                "stdout_path": evidence.stdout_path,
                "stderr_path": evidence.stderr_path,
            }
        )

    return BundleManifest(
        run_id=run_id,
        task_id=task_id,
        product_artifacts=product_artifacts,
        agent_versions=agent_versions,
        skill_versions=skill_versions,
        evidence_indexes=evidence_indexes,
        report_indexes=reports,
        checksums=checksums,
        model_summary=model_summary,
        env_profile_summary=env_profile_summary,
    )
