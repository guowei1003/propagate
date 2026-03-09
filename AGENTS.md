# Propagate - AI Task Execution System

## Project Overview

Propagate is a low-dependency AI task execution system with a built-in web UI. It implements a controlled agent orchestration workflow where AI agents execute tasks through a structured pipeline rather than free-form interactions.

### Key Features

- **Requirement Analysis**: Parse user prompts into structured requirements with clarification rounds
- **Task Decomposition**: Break down tasks into subtasks with dependency handling (DAG)
- **Parallel Execution**: Background worker executes independent subtasks concurrently
- **Review/Test Loop**: Every subtask goes through code review and testing before completion
- **Real-time Events**: SSE-based event streaming for live task progress
- **Final Reports**: Automatic generation of execution reports and artifact persistence

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| Database | SQLite |
| Frontend | Jinja2 + HTMX + SSE |
| Background Worker | Thread-based pool executor |

## Project Structure

```
propagate/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration and settings
│   ├── db.py                # SQLite database connection
│   ├── enums.py             # Task and subtask status constants
│   ├── domain/
│   │   └── models.py        # Data transfer objects (DTOs)
│   ├── api/routes/          # HTTP endpoints
│   │   ├── tasks.py         # Task CRUD APIs
│   │   ├── events.py        # SSE event streaming
│   │   ├── pages.py         # HTML page routes
│   │   └── env_profiles.py  # Environment profile APIs
│   ├── orchestrator/
│   │   └── task_orchestrator.py  # Core state machine
│   ├── agents/              # AI agent implementations
│   │   ├── requirement_analyzer.py
│   │   ├── task_decomposer.py
│   │   ├── task_evaluator.py
│   │   ├── executor.py
│   │   ├── code_review.py
│   │   ├── tester.py
│   │   └── reporter.py
│   ├── workers/
│   │   └── engine.py        # Background worker engine
│   ├── repositories/        # Data access layer
│   ├── services/            # Cross-cutting services
│   │   ├── llm_service.py   # LLM provider abstraction
│   │   ├── event_service.py # Event publishing
│   │   └── artifact_service.py
│   └── web/
│       ├── templates/       # Jinja2 HTML templates
│       └── static/          # CSS and JavaScript
├── data/
│   └── artifacts/           # Generated artifacts storage
├── migrations/
│   └── 001_initial_schema.sql
├── docs/
│   ├── ai-task-execution-blueprint.md
│   └── backend-module-blueprint.md
├── scripts/
│   └── run_api.py           # Application launcher
└── tests/
```

## Build and Run

### Install Dependencies

```bash
python3 -m pip install -e .
```

### Start the Application

```bash
python3 scripts/run_api.py
```

### Access the UI

Open http://127.0.0.1:8000/tasks in your browser.

### Run Tests

```bash
python3 -m pytest
```

## Configuration

Configuration is loaded from environment variables. Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

### Key Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER_TYPE` | `demo` or `openai_compatible` | `demo` |
| `LLM_API_BASE_URL` | API endpoint for OpenAI-compatible providers | - |
| `LLM_API_KEY` | API key | - |
| `LLM_DEFAULT_MODEL` | Default model name | `gpt-4o-mini` |
| `MAX_WORKER_CONCURRENCY` | Max parallel subtask executions | `3` |
| `WORKER_POLL_INTERVAL_SEC` | Worker polling interval | `1.0` |

### LLM Provider Modes

1. **Demo Mode** (`LLM_PROVIDER_TYPE=demo`): Returns mock responses, no external API calls
2. **OpenAI Compatible** (`LLM_PROVIDER_TYPE=openai_compatible`): Connects to OpenAI, Azure OpenAI, Ollama, or any OpenAI-compatible API

## Core Workflows

### Task Lifecycle

```
CREATED → REQUIREMENT_ANALYZING → [WAITING_USER_INPUT] → TASK_DECOMPOSING → 
TASK_EVALUATING → SUBTASK_RUNNING → REPORTING → COMPLETED/PARTIAL_SUCCESS/FAILED
```

### Subtask Lifecycle

```
PENDING → READY → RUNNING → [RETRY_PENDING] → COMPLETED
                     ↓
              NEEDS_HUMAN_REVIEW (when max retries exceeded)
```

### Execution Loop

Each subtask follows this pattern:

```
Executor Agent → Code Review → Test Agent
                     ↓              ↓
                  RETRY          RETRY
                     ↓              ↓
               NEEDS_HUMAN_REVIEW (on failure)
```

## Agent System

| Agent | Purpose | Input | Output |
|-------|---------|-------|--------|
| Requirement Analyzer | Parse prompt, find ambiguities | Raw prompt, answers | Structured requirement, questions |
| Task Decomposer | Create subtasks | Structured requirement | Subtask list with dependencies |
| Task Evaluator | Assign execution strategy | Subtask content | Agent template, skills, timeout |
| Executor | Execute subtask | Task context | Code/artifacts |
| Code Review | Quality check | Execution output | Pass/fail with issues |
| Test Agent | Validate execution | Code, test commands | Test results |
| Reporter | Generate final report | All task data | Markdown report |

## Architecture Principles

1. **Orchestration-First**: All state changes flow through `TaskOrchestrator`
2. **State-Driven**: Every critical step has persistent state for recovery
3. **Review-Required**: All outputs must pass review and test gates
4. **Human Fallback**: Unclear requirements or repeated failures trigger human intervention
5. **Minimal Dependencies**: No external workflow engines, message queues, or object stores

## API Endpoints

### Task APIs

- `POST /api/tasks` - Create new task
- `GET /api/tasks` - List tasks (paginated)
- `GET /api/tasks/{task_id}` - Get task details
- `POST /api/tasks/{task_id}/clarifications/{round_id}/answer` - Submit clarification answers

### Event APIs

- `GET /api/tasks/{task_id}/events` - Get event history
- `GET /api/tasks/{task_id}/stream` - SSE event stream

### Environment Profiles

- `GET /api/env-profiles` - List profiles
- `POST /api/env-profiles` - Create profile
- `PUT /api/env-profiles/{id}` - Update profile

## Database Schema

The system uses SQLite with the following core tables:

- `tasks` - Main task records
- `task_requirements` - Structured requirements (versioned)
- `clarification_rounds` - Q&A rounds for requirement clarification
- `sub_tasks` - Decomposed subtasks
- `sub_task_dependencies` - DAG edges between subtasks
- `agent_runs` - Agent execution logs
- `task_events` - Event log for SSE streaming
- `artifacts` - Generated file metadata
- `task_reports` - Final reports
- `env_profiles` - LLM and environment configuration

## Development Notes

- The current agent implementation is deterministic and local-first (demo mode)
- `llm_service.py` abstracts LLM calls for easy provider switching
- All agent outputs must be structured; schema validation is enforced
- Worker uses `ThreadPoolExecutor` for concurrent subtask execution
- SSE streaming polls the database for new events

## Further Reading

- `docs/ai-task-execution-blueprint.md` - Full system design document
- `docs/backend-module-blueprint.md` - Backend module design details
