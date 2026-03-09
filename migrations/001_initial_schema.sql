BEGIN;

CREATE TABLE env_profiles (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    default_model VARCHAR(100) NOT NULL,
    review_model VARCHAR(100),
    test_model VARCHAR(100),
    max_concurrency INTEGER NOT NULL DEFAULT 2 CHECK (max_concurrency > 0),
    default_timeout_sec INTEGER NOT NULL DEFAULT 600 CHECK (default_timeout_sec > 0),
    max_retries INTEGER NOT NULL DEFAULT 3 CHECK (max_retries >= 0),
    enable_auto_sub_agents BOOLEAN NOT NULL DEFAULT FALSE,
    enable_docker_sandbox BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    prompt TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_phase VARCHAR(50) NOT NULL,
    env_profile_id UUID REFERENCES env_profiles(id),
    progress_percent NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    failure_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_updated_at ON tasks(updated_at DESC);

CREATE TABLE task_requirements (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
    goal TEXT,
    scope TEXT,
    inputs_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    outputs_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    constraints_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    acceptance_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    missing_info_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (task_id, version)
);

CREATE INDEX idx_task_requirements_task_id ON task_requirements(task_id);

CREATE TABLE clarification_rounds (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL,
    questions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    answers_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    answered_at TIMESTAMPTZ
);

CREATE INDEX idx_clarification_rounds_task_id ON clarification_rounds(task_id);
CREATE INDEX idx_clarification_rounds_status ON clarification_rounds(status);

CREATE TABLE sub_tasks (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 100,
    sequence_no INTEGER NOT NULL DEFAULT 0,
    agent_template VARCHAR(100) NOT NULL,
    skill_bindings_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    acceptance_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    input_context_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    max_retries INTEGER NOT NULL DEFAULT 3 CHECK (max_retries >= 0),
    timeout_sec INTEGER NOT NULL DEFAULT 600 CHECK (timeout_sec > 0),
    locked_by VARCHAR(100),
    locked_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sub_tasks_task_id ON sub_tasks(task_id);
CREATE INDEX idx_sub_tasks_status ON sub_tasks(status);
CREATE INDEX idx_sub_tasks_ready_queue ON sub_tasks(status, priority, created_at);
CREATE UNIQUE INDEX idx_sub_tasks_task_sequence ON sub_tasks(task_id, sequence_no);

CREATE TABLE sub_task_dependencies (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    from_sub_task_id UUID NOT NULL REFERENCES sub_tasks(id) ON DELETE CASCADE,
    to_sub_task_id UUID NOT NULL REFERENCES sub_tasks(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (from_sub_task_id, to_sub_task_id),
    CHECK (from_sub_task_id <> to_sub_task_id)
);

CREATE INDEX idx_sub_task_dependencies_task_id ON sub_task_dependencies(task_id);
CREATE INDEX idx_sub_task_dependencies_to_sub_task_id ON sub_task_dependencies(to_sub_task_id);

CREATE TABLE agent_runs (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    sub_task_id UUID REFERENCES sub_tasks(id) ON DELETE CASCADE,
    agent_type VARCHAR(100) NOT NULL,
    model VARCHAR(100),
    status VARCHAR(50) NOT NULL,
    step_no INTEGER NOT NULL DEFAULT 1 CHECK (step_no > 0),
    input_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_agent_runs_task_id ON agent_runs(task_id);
CREATE INDEX idx_agent_runs_sub_task_id ON agent_runs(sub_task_id);
CREATE INDEX idx_agent_runs_status ON agent_runs(status);

CREATE TABLE task_events (
    id BIGSERIAL PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    sub_task_id UUID REFERENCES sub_tasks(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    level VARCHAR(20) NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_task_events_task_id_id ON task_events(task_id, id);
CREATE INDEX idx_task_events_sub_task_id_id ON task_events(sub_task_id, id);
CREATE INDEX idx_task_events_created_at ON task_events(created_at DESC);

CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    sub_task_id UUID REFERENCES sub_tasks(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    path TEXT NOT NULL,
    summary TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_artifacts_task_id ON artifacts(task_id);
CREATE INDEX idx_artifacts_sub_task_id ON artifacts(sub_task_id);
CREATE INDEX idx_artifacts_type ON artifacts(type);

CREATE TABLE task_reports (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL UNIQUE REFERENCES tasks(id) ON DELETE CASCADE,
    report_markdown TEXT NOT NULL,
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE sub_task_review_results (
    id UUID PRIMARY KEY,
    sub_task_id UUID NOT NULL REFERENCES sub_tasks(id) ON DELETE CASCADE,
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    decision VARCHAR(30) NOT NULL,
    issues_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sub_task_review_results_sub_task_id ON sub_task_review_results(sub_task_id);

CREATE TABLE sub_task_test_results (
    id UUID PRIMARY KEY,
    sub_task_id UUID NOT NULL REFERENCES sub_tasks(id) ON DELETE CASCADE,
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    passed BOOLEAN NOT NULL,
    command TEXT,
    log_excerpt TEXT,
    summary TEXT,
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sub_task_test_results_sub_task_id ON sub_task_test_results(sub_task_id);
CREATE INDEX idx_sub_task_test_results_passed ON sub_task_test_results(passed);

COMMIT;
