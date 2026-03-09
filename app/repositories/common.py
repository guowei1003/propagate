from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def dumps_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)


def row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row is not None else {}

