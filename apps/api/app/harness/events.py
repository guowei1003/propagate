from __future__ import annotations

from typing import Any


def build_event(category: str, name: str, message: str, **payload: Any) -> dict[str, Any]:
    return {
        "category": category,
        "name": name,
        "message": message,
        "payload": payload,
    }
