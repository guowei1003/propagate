# Propagate - AI Task Execution System

## Project Overview

Propagate is a low-dependency AI task execution system with a built-in web UI. AI agents execute tasks through a structured pipeline: create task → AI generates script → Docker sandbox execution → view results.

### Key Features

- **Task CRUD**: Create, list, inspect, delete tasks via REST API
- **Docker Sandbox**: Subtasks execute in isolated containers (`--network none`)
- **LLM Integration**: Demo mode (mock) / OpenAI / Ollama
- **SSE Event Stream**: Real-time task progress in the browser
- **Environment Profiles**: Configurable LLM environments per task
- **React SPA**: Modern dark-theme UI with hash-based routing

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| Database | PostgreSQL |
| Frontend | React + Vite + TypeScript |
| Runtime | Docker containers |
| Deployment | Docker Compose |

## Project Structure

```
propagate/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app + lifespan (auto-migrate tables)
│   │   ├── config.py        # Settings from environment variables
│   │   ├── db.py            # SQLAlchemy async engine + session
│   │   ├── models.py        # SQLAlchemy models (Task, TaskLog, TaskResult, Profile)
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── tasks.py     # /api/tasks CRUD + /api/tasks/{id}/stream SSE
│   │   │   ├── profiles.py  # /api/profiles CRUD
│   │   │   └── events.py    # In-memory SSE subscriber registry
│   │   └── services/
│   │       ├── task_service.py  # Business logic
│   │       ├── worker.py       # Docker sandbox executor (async polling)
│   │       └── llm.py          # LLM abstraction (demo / openai / ollama)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py               # Dev entry point
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Root component + hash router
│   │   ├── main.tsx         # Entry point with ToastProvider
│   │   ├── theme.ts         # Theme system (light / dark / system)
│   │   ├── presenters.ts    # Data formatting helpers
│   │   ├── components/
│   │   │   ├── Layout.tsx        # Sidebar + topbar
│   │   │   ├── TaskList.tsx      # Card list + filter + search
│   │   │   ├── TaskDetail.tsx    # Tabbed: overview / logs / result
│   │   │   ├── TaskCreate.tsx    # Modal form
│   │   │   ├── ProfilesPage.tsx  # Environment config CRUD
│   │   │   ├── MetricStrip.tsx   # KPI cards
│   │   │   ├── StatusBadge.tsx
│   │   │   ├── ThemeToggle.tsx
│   │   │   ├── ToastViewport.tsx
│   │   │   └── notifications/
│   │   │       └── ToastProvider.tsx
│   │   ├── lib/
│   │   │   ├── api.ts       # fetch wrapper
│   │   │   └── toast.ts     # Toast context types
│   │   └── styles/          # CSS (tokens, base, layout, components, pages)
│   ├── index.html
│   ├── vite.config.ts       # Proxy /api to backend:8000
│   └── Dockerfile           # Node build + nginx serving
├── deploy/
│   ├── docker-compose.yml          # Production (postgres + api + frontend)
│   ├── docker-compose.dev.yml      # Development (source mount + hot reload)
│   ├── docker/
│   │   ├── api.Dockerfile
│   │   ├── frontend.Dockerfile     # Node → nginx
│   │   ├── runner.Dockerfile       # Minimal sandbox container
│   │   └── nginx.conf              # SPA + /api/ proxy
│   ├── scripts/
│   │   ├── init_db.sh      # DB init + migration
│   │   ├── build.sh        # Build all 3 images
│   │   ├── deploy.sh       # deploy [dev|production]
│   │   ├── restart.sh      # restart [service-name]
│   │   └── clean.sh        # Remove containers + volumes
│   └── .env.example
└── README.md
```

## Build and Run

### Docker Compose (Production)

```bash
./deploy/scripts/build.sh
./deploy/scripts/deploy.sh production
# Frontend: http://localhost
# API:      http://localhost:8000
# Docs:     http://localhost:8000/docs
```

### Docker Compose (Development)

```bash
./deploy/scripts/deploy.sh dev
# Frontend dev: http://localhost:3000
# API:          http://localhost:8000
```

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/propagate
python3 run.py

# Frontend
cd frontend
npm install
npm run dev
```

## API Endpoints

### Tasks

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/tasks` | List tasks (filter by `status`) |
| `POST` | `/api/tasks` | Create a task |
| `GET` | `/api/tasks/{id}` | Get task detail |
| `DELETE` | `/api/tasks/{id}` | Delete a task |
| `GET` | `/api/tasks/{id}/stream` | SSE event stream |
| `GET` | `/api/tasks/{id}/events` | Historical event list |

### Profiles

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/profiles` | List profiles |
| `POST` | `/api/profiles` | Create profile |
| `GET` | `/api/profiles/{id}` | Get profile |
| `PUT` | `/api/profiles/{id}` | Update profile |
| `DELETE` | `/api/profiles/{id}` | Delete profile |

## LLM Providers

- `demo` (default): Mock responses based on prompt content
- `openai`: Set `LLM_PROVIDER=openai` + `LLM_API_KEY`
- `ollama`: Set `LLM_PROVIDER=ollama` + `LLM_API_BASE=http://localhost:11434/v1`

## Configuration

Copy `deploy/.env.example` → `.env` and configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `LLM_PROVIDER` | `demo` | `demo` / `openai` / `ollama` |
| `LLM_API_BASE` | - | API base URL for OpenAI-compatible |
| `LLM_API_KEY` | - | API key |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `WORKER_CONCURRENCY` | `3` | Max parallel executions |
| `RUNNER_IMAGE` | `propagate-runner:latest` | Sandbox container image |