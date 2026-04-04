from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Iterator

from app.v2.core.config import v2_settings
from app.v2.core.errors import DependencyError


def dumps_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _import_psycopg():
    try:
        import psycopg  # type: ignore
        from psycopg.rows import dict_row  # type: ignore
    except ModuleNotFoundError as exc:
        raise DependencyError(
            "V2 PostgreSQL runtime requires psycopg. Install psycopg[binary] before starting the app."
        ) from exc
    return psycopg, dict_row


@contextmanager
def get_connection() -> Iterator[Any]:
    psycopg, dict_row = _import_psycopg()
    conn = psycopg.connect(v2_settings.database_url, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def transaction(connection: Any | None = None) -> Iterator[Any]:
    if connection is not None:
        yield connection
        return
    with get_connection() as conn:
        yield conn


def fetch_one(query: str, params: tuple[Any, ...] = (), *, connection: Any | None = None) -> dict[str, Any] | None:
    with transaction(connection) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
    return dict(row) if row else None



def fetch_all(query: str, params: tuple[Any, ...] = (), *, connection: Any | None = None) -> list[dict[str, Any]]:
    with transaction(connection) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
    return [dict(row) for row in rows]



def execute(query: str, params: tuple[Any, ...] = (), *, connection: Any | None = None) -> None:
    with transaction(connection) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
