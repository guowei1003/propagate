export type TaskSummary = {
  id: string;
  title: string;
  goal: string;
  approval_mode: string;
  latest_run_id: string | null;
  created_at: string;
  updated_at: string;
};

export type TaskDetail = TaskSummary & {
  latest_run?: {
    id: string;
    status: string;
    thread_id: string;
  } | null;
};

export type RunStep = {
  id: string;
  step_id: string;
  position: number;
  title: string;
  kind: string;
  assigned_agent_id: string;
  status: string;
  attempts: number;
  approval_required: boolean;
  expected_artifacts: string[];
  dependencies: string[];
  result: Record<string, unknown> | null;
};

export type Approval = {
  id: string;
  run_id: string;
  step_id: string;
  reason: string;
  status: string;
  decision: string | null;
  comment: string | null;
  requested_at: string;
  resolved_at: string | null;
};

export type Artifact = {
  id: string;
  run_id: string;
  step_id: string | null;
  name: string;
  artifact_type: string;
  mime_type: string;
  storage_path: string;
  sha256: string;
  details: Record<string, unknown>;
  created_at: string;
};

export type RunEvent = {
  id: number;
  run_id: string;
  sequence: number;
  category: string;
  name: string;
  message: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type RunDetail = {
  id: string;
  task_id: string;
  status: string;
  thread_id: string;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  mission: Record<string, unknown> | null;
  selected_agents: Array<Record<string, unknown>>;
  execution_plan: Record<string, unknown> | null;
  verification_summary: Record<string, unknown> | null;
  warnings: string[];
  interrupt_payload: Record<string, unknown> | null;
  steps: RunStep[];
  approvals: Approval[];
  artifacts: Artifact[];
};

export type AgentSpec = {
  id: string;
  name: string;
  role: string;
  capabilities: string[];
  allowed_tools: string[];
  allowed_step_kinds: string[];
  requires_approval_for: string[];
  max_turns: number;
  model_tier: string;
};

export type Profile = {
  id: string;
  name: string;
  model_provider: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  http_allowlist_domains: string[];
  http_allowlist_methods: string[];
  sandbox_cpu_limit: number;
  sandbox_memory_limit_mb: number;
  step_timeout_sec: number;
  requires_human_approval_for_high_risk: boolean;
  created_at: string;
  updated_at: string;
};
