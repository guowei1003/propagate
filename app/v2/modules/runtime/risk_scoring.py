from __future__ import annotations

from app.v2.core.models import CapabilitySpec


HIGH_RISK_COMMAND_TOKENS = ("sudo", "rm -rf", "chmod 777", "chown", "mkfs", "dd ")
NETWORK_TOKENS = ("curl ", "wget ", "http://", "https://")
ESCAPE_PATH_TOKENS = ("/", "..", "~")


def score_capability_risk(spec: CapabilitySpec) -> int:
    score = 0
    combined = " ".join(
        [spec.instructions, *spec.allowed_commands, *spec.allowed_file_scope, *spec.risk_tags]
    ).lower()

    if any(token in combined for token in HIGH_RISK_COMMAND_TOKENS):
        score += 6
    if any(token in combined for token in NETWORK_TOKENS):
        score += 3
    if any(scope.strip() in ESCAPE_PATH_TOKENS or scope.strip().startswith("/") for scope in spec.allowed_file_scope):
        score += 2
    if "run_command" in spec.allowed_tools:
        score += 1
    if any(tag in {"privileged", "network", "destructive"} for tag in spec.risk_tags):
        score += 2
    return score
