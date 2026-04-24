from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ApprovalDecisionRequest(BaseModel):
    approval_id: UUID
    comment: str | None = None


class ApprovalResponse(BaseModel):
    id: UUID
    run_id: UUID
    step_id: str
    reason: str
    status: str
    decision: str | None
    comment: str | None
    requested_at: datetime
    resolved_at: datetime | None = None
