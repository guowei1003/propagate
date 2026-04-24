from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.db import Base
from app.models.task import utcnow


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    model_provider: Mapped[str] = mapped_column(String(64), default="mock", nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), default="gpt-4.1-mini", nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4000, nullable=False)
    http_allowlist_domains: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    http_allowlist_methods: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    sandbox_cpu_limit: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    sandbox_memory_limit_mb: Mapped[int] = mapped_column(Integer, default=512, nullable=False)
    step_timeout_sec: Mapped[int] = mapped_column(Integer, default=180, nullable=False)
    requires_human_approval_for_high_risk: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    runs: Mapped[list["TaskRun"]] = relationship("TaskRun", back_populates="profile")
