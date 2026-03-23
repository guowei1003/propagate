# Propagate

Propagate is a low-dependency AI task execution system with a built-in UI, controlled agent orchestration, task clarification, subtask execution, review/test loops, and final report generation.

## Features

- Create tasks from a prompt in the web UI
- Requirement analysis with clarification rounds
- Task decomposition into subtasks with dependency handling
- Dynamic temporary agent templates and skill binding per subtask
- Isolated runtime workspace materialization for every subtask
- Background worker that executes subtasks
- Built-in review and test loop with retries
- Real-time task event streaming over SSE
- Environment profile management
- Final report generation and artifact persistence

## Stack

- FastAPI
- Jinja2 templates
- SQLite
- Thread-based background worker

## Run

1. Install dependencies:

```bash
python3 -m pip install -e .
```

2. Start the app:

```bash
python3 scripts/run_api.py
```

3. Open:

```text
http://127.0.0.1:8000/tasks
```

## Notes

- The current agent implementation is deterministic and local-first so the product can run without external model access.
- The `llm_service` interface is already isolated so a real model provider can be added later without changing the workflow design.
