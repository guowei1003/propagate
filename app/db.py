from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import settings


def _adapt_dict(value: dict) -> str:
    return json.dumps(value)


def _adapt_list(value: list) -> str:
    return json.dumps(value)


sqlite3.register_adapter(dict, _adapt_dict)
sqlite3.register_adapter(list, _adapt_list)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_parent(settings.database_path)
    conn = sqlite3.connect(settings.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    ensure_parent(settings.database_path)
    with transaction() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS env_profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                provider_type TEXT NOT NULL DEFAULT 'demo',
                api_base_url TEXT,
                api_key TEXT,
                default_model TEXT NOT NULL,
                review_model TEXT,
                test_model TEXT,
                temperature REAL NOT NULL DEFAULT 0.2,
                max_concurrency INTEGER NOT NULL DEFAULT 2,
                default_timeout_sec INTEGER NOT NULL DEFAULT 300,
                max_retries INTEGER NOT NULL DEFAULT 2,
                enable_auto_sub_agents INTEGER NOT NULL DEFAULT 0,
                enable_docker_sandbox INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                title_auto_generated INTEGER NOT NULL DEFAULT 1,
                prompt TEXT NOT NULL,
                status TEXT NOT NULL,
                current_phase TEXT NOT NULL,
                env_profile_id TEXT NOT NULL REFERENCES env_profiles(id),
                progress_percent REAL NOT NULL DEFAULT 0,
                failure_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS task_requirements (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                version INTEGER NOT NULL,
                goal TEXT,
                scope TEXT,
                inputs_json TEXT NOT NULL,
                outputs_json TEXT NOT NULL,
                constraints_json TEXT NOT NULL,
                acceptance_json TEXT NOT NULL,
                missing_info_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(task_id, version)
            );

            CREATE TABLE IF NOT EXISTS clarification_rounds (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                status TEXT NOT NULL,
                questions_json TEXT NOT NULL,
                answers_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                answered_at TEXT
            );

            CREATE TABLE IF NOT EXISTS sub_tasks (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 100,
                sequence_no INTEGER NOT NULL DEFAULT 0,
                agent_template TEXT NOT NULL,
                skill_bindings_json TEXT NOT NULL,
                acceptance_json TEXT NOT NULL,
                input_context_json TEXT NOT NULL,
                output_summary_json TEXT NOT NULL,
                retry_count INTEGER NOT NULL DEFAULT 0,
                max_retries INTEGER NOT NULL DEFAULT 2,
                timeout_sec INTEGER NOT NULL DEFAULT 300,
                started_at TEXT,
                completed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sub_task_dependencies (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                from_sub_task_id TEXT NOT NULL REFERENCES sub_tasks(id) ON DELETE CASCADE,
                to_sub_task_id TEXT NOT NULL REFERENCES sub_tasks(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                UNIQUE(from_sub_task_id, to_sub_task_id)
            );

            CREATE TABLE IF NOT EXISTS task_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                sub_task_id TEXT REFERENCES sub_tasks(id) ON DELETE CASCADE,
                event_type TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                sub_task_id TEXT REFERENCES sub_tasks(id) ON DELETE CASCADE,
                artifact_type TEXT NOT NULL,
                path TEXT NOT NULL,
                summary TEXT,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_runs (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                sub_task_id TEXT REFERENCES sub_tasks(id) ON DELETE CASCADE,
                agent_type TEXT NOT NULL,
                model TEXT,
                status TEXT NOT NULL,
                input_json TEXT NOT NULL,
                output_json TEXT NOT NULL,
                error_json TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS sub_task_review_results (
                id TEXT PRIMARY KEY,
                sub_task_id TEXT NOT NULL REFERENCES sub_tasks(id) ON DELETE CASCADE,
                decision TEXT NOT NULL,
                issues_json TEXT NOT NULL,
                summary TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sub_task_test_results (
                id TEXT PRIMARY KEY,
                sub_task_id TEXT NOT NULL REFERENCES sub_tasks(id) ON DELETE CASCADE,
                passed INTEGER NOT NULL,
                command_text TEXT,
                log_excerpt TEXT,
                summary TEXT,
                details_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS task_reports (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL UNIQUE REFERENCES tasks(id) ON DELETE CASCADE,
                report_markdown TEXT NOT NULL,
                summary_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_sub_tasks_task_id ON sub_tasks(task_id);
            CREATE INDEX IF NOT EXISTS idx_sub_tasks_status ON sub_tasks(status);
            CREATE INDEX IF NOT EXISTS idx_events_task_id_id ON task_events(task_id, id);
            """
        )
        _ensure_column(conn, "env_profiles", "provider_type", "TEXT NOT NULL DEFAULT 'demo'")
        _ensure_column(conn, "env_profiles", "api_base_url", "TEXT")
        _ensure_column(conn, "env_profiles", "api_key", "TEXT")
        _ensure_column(conn, "env_profiles", "temperature", "REAL NOT NULL DEFAULT 0.2")
        _ensure_column(conn, "tasks", "title_auto_generated", "INTEGER NOT NULL DEFAULT 1")


def _ensure_column(conn: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
    columns = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name in columns:
        return
    conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
