BEGIN;

CREATE TABLE IF NOT EXISTS env_profiles (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    provider_type VARCHAR(50) NOT NULL,
    api_base_url TEXT,
    api_key TEXT,
    default_model VARCHAR(200) NOT NULL,
    review_model VARCHAR(200),
    test_model VARCHAR(200),
    capability_generation_model VARCHAR(200),
    report_model VARCHAR(200),
    temperature DOUBLE PRECISION NOT NULL DEFAULT 0.2,
    default_timeout_sec INTEGER NOT NULL DEFAULT 300,
    max_retries INTEGER NOT NULL DEFAULT 2,
    max_concurrency INTEGER NOT NULL DEFAULT 2,
    enable_docker_sandbox BOOLEAN NOT NULL DEFAULT TRUE,
    enable_auto_sub_agents BOOLEAN NOT NULL DEFAULT TRUE,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    prompt TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_phase VARCHAR(50) NOT NULL,
    env_profile_id UUID NOT NULL REFERENCES env_profiles(id),
    model_overrides_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS runs (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    current_phase VARCHAR(50) NOT NULL,
    env_profile_id UUID NOT NULL REFERENCES env_profiles(id),
    model_overrides_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS task_requirements (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    goal TEXT NOT NULL,
    scope TEXT NOT NULL,
    inputs_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    outputs_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    constraints_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    acceptance_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    missing_info_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(task_id, version)
);

CREATE TABLE IF NOT EXISTS clarification_rounds (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL,
    questions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    answers_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    answered_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS capabilities (
    id UUID PRIMARY KEY,
    type VARCHAR(20) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    latest_version_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS capability_versions (
    id UUID PRIMARY KEY,
    capability_id UUID NOT NULL REFERENCES capabilities(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    status VARCHAR(30) NOT NULL,
    content_hash VARCHAR(128) NOT NULL,
    rendered_spec JSONB NOT NULL DEFAULT '{}'::jsonb,
    risk_score INTEGER NOT NULL DEFAULT 0,
    source_task_id UUID,
    source_run_id UUID,
    default_model_selector VARCHAR(200),
    generation_model VARCHAR(200),
    generation_prompt TEXT,
    generation_raw_output TEXT,
    validation_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE capabilities
    DROP CONSTRAINT IF EXISTS fk_capabilities_latest_version;
ALTER TABLE capabilities
    ADD CONSTRAINT fk_capabilities_latest_version
    FOREIGN KEY (latest_version_id) REFERENCES capability_versions(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS approval_records (
    id UUID PRIMARY KEY,
    capability_version_id UUID NOT NULL REFERENCES capability_versions(id) ON DELETE CASCADE,
    decision VARCHAR(20) NOT NULL,
    approver VARCHAR(120) NOT NULL,
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sub_tasks (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    sequence_no INTEGER NOT NULL DEFAULT 0,
    priority INTEGER NOT NULL DEFAULT 100,
    capability_bindings_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    acceptance_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    input_context_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 2,
    timeout_sec INTEGER NOT NULL DEFAULT 300,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sub_task_dependencies (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    from_sub_task_id UUID NOT NULL REFERENCES sub_tasks(id) ON DELETE CASCADE,
    to_sub_task_id UUID NOT NULL REFERENCES sub_tasks(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(from_sub_task_id, to_sub_task_id)
);

CREATE TABLE IF NOT EXISTS task_events (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    sub_task_id UUID REFERENCES sub_tasks(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    level VARCHAR(20) NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS execution_evidence (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    sub_task_id UUID NOT NULL REFERENCES sub_tasks(id) ON DELETE CASCADE,
    command TEXT NOT NULL,
    exit_code INTEGER NOT NULL,
    stdout_path TEXT NOT NULL,
    stderr_path TEXT NOT NULL,
    output_files_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    file_hashes_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    container_metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS artifacts (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    sub_task_id UUID REFERENCES sub_tasks(id) ON DELETE CASCADE,
    artifact_type VARCHAR(50) NOT NULL,
    path TEXT NOT NULL,
    summary TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS task_reports (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    run_id UUID NOT NULL UNIQUE REFERENCES runs(id) ON DELETE CASCADE,
    report_markdown TEXT NOT NULL,
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sub_task_review_results (
    id UUID PRIMARY KEY,
    sub_task_id UUID NOT NULL REFERENCES sub_tasks(id) ON DELETE CASCADE,
    decision VARCHAR(30) NOT NULL,
    issues_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sub_task_test_results (
    id UUID PRIMARY KEY,
    sub_task_id UUID NOT NULL REFERENCES sub_tasks(id) ON DELETE CASCADE,
    passed BOOLEAN NOT NULL,
    command_text TEXT,
    log_excerpt TEXT,
    summary TEXT,
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bundles (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL UNIQUE REFERENCES runs(id) ON DELETE CASCADE,
    bundle_dir TEXT NOT NULL,
    manifest_path TEXT NOT NULL,
    manifest_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_v2_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_v2_runs_task_id ON runs(task_id);
CREATE INDEX IF NOT EXISTS idx_v2_sub_tasks_run_id ON sub_tasks(run_id);
CREATE INDEX IF NOT EXISTS idx_v2_task_events_run_id ON task_events(run_id, created_at);

COMMIT;
