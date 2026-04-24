from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from sqlalchemy.types import Uuid

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    deliverables: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    approval_mode: Mapped[str] = mapped_column(String(32), default="high_risk", nullable=False)
    latest_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("task_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    runs: Mapped[list["TaskRun"]] = relationship(
        "TaskRun",
        back_populates="task",
        foreign_keys="TaskRun.task_id",
        cascade="all, delete-orphan",
        order_by="TaskRun.created_at.desc()",
    )
