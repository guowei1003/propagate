from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    status: str
    summary: str
    artifacts: list[str]
    payload: dict[str, Any]
