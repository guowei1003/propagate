from __future__ import annotations


class InvalidCapabilityTransition(ValueError):
    pass


def apply_approval_decision(current_status: str, decision: str) -> str:
    normalized_status = current_status.strip().lower()
    normalized_decision = decision.strip().lower()

    if normalized_status != "pending_approval":
        raise InvalidCapabilityTransition(
            f"Only pending_approval capabilities can be reviewed, got {current_status}."
        )
    if normalized_decision == "approve":
        return "approved"
    if normalized_decision == "reject":
        return "rejected"
    raise InvalidCapabilityTransition(f"Unsupported approval decision: {decision}")
