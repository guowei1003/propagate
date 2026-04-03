from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


HIGH_RISK_TOKENS = ("sudo", "rm -rf", "chmod 777", "chown ", "mkfs", "dd ", "shutdown", "reboot")
NETWORK_TOKENS = ("curl ", "wget ", "http://", "https://")


class GuardrailViolation(ValueError):
    pass


@dataclass(slots=True)
class GuardrailVerdict:
    allowed: bool
    reason: str = ""


def _path_within_scope(path: str, scope: str) -> bool:
    target = PurePosixPath(path)
    allowed_root = PurePosixPath(scope)
    try:
        target.relative_to(allowed_root)
        return True
    except ValueError:
        return False


def preflight_guard(
    *,
    command: str,
    allowed_commands: list[str],
    allowed_file_scope: list[str],
    requested_paths: list[str],
) -> GuardrailVerdict:
    normalized = command.strip()
    if normalized not in [item.strip() for item in allowed_commands]:
        raise GuardrailViolation(f"Command is not whitelisted: {normalized}")
    lowered = normalized.lower()
    if any(token in lowered for token in HIGH_RISK_TOKENS):
        raise GuardrailViolation(f"High-risk command blocked: {normalized}")
    if any(token in lowered for token in NETWORK_TOKENS):
        raise GuardrailViolation(f"Network access is not allowed: {normalized}")
    for path in requested_paths:
        if not any(_path_within_scope(path, scope) for scope in allowed_file_scope):
            raise GuardrailViolation(f"Requested path is outside allowed scope: {path}")
    return GuardrailVerdict(allowed=True)
