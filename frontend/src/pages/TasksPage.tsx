import { useEffect, useRef, useState } from "react";

import { MetricStrip } from "../components/MetricStrip";
import { TaskActionInbox } from "../components/tasks/TaskActionInbox";
import { TaskInspector } from "../components/tasks/TaskInspector";
import { TaskQuickCreateModal } from "../components/tasks/TaskQuickCreateModal";
import { TaskQueue } from "../components/tasks/TaskQueue";
import { getErrorMessage, getJson, postJson } from "../lib/api";
import { buildTaskMetrics, pickPreferredTask } from "../lib/presenters";

type EnvProfile = { id: string; name: string };
type TaskSummary = {
  id: string;
  title: string;
  created_at: string;
  status: string;
  current_phase: string;
  env_profile?: { name: string } | null;
  run?: { id: string } | null;
  clarification_rounds?: Array<{ id: string; status: string; questions?: Array<{ key: string; question: string }> }>;
  requirement?: Record<string, unknown> | null;
  subtasks?: Array<{ id: string; name: string; status: string }>;
};

type Props = {
  meta: {
    eyebrow: string;
    title: string;
    description: string;
  };
  onNavigate: (
    view: "tasks" | "runs" | "capabilities" | "profiles" | "artifacts",
    context?: { taskId?: string; runId?: string }
  ) => void;
  onStatsChange: (update: { taskCount?: number; profileCount?: number; pendingCapabilities?: number }) => void;
};

export function TasksPage({ meta, onNavigate, onStatsChange }: Props) {
  const successTimeoutRef = useRef<number | null>(null);
  const queueSectionRef = useRef<HTMLDivElement | null>(null);
  const [prompt, setPrompt] = useState("");
  const [envProfileId, setEnvProfileId] = useState("");
  const [modelOverrides, setModelOverrides] = useState({
    review: "",
    test: "",
    report: "",
    capability_generation: ""
  });
  const [profiles, setProfiles] = useState<EnvProfile[]>([]);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [selectedTask, setSelectedTask] = useState<TaskSummary | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [pageErrorMessage, setPageErrorMessage] = useState("");
  const [createErrorMessage, setCreateErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  function clearSuccessTimer() {
    if (successTimeoutRef.current) {
      window.clearTimeout(successTimeoutRef.current);
      successTimeoutRef.current = null;
    }
  }

  async function refresh(options?: { preferredTaskId?: string; errorScope?: "page" | "create" }) {
    setIsRefreshing(true);
    if (options?.errorScope === "create") {
      setCreateErrorMessage("");
    } else {
      setPageErrorMessage("");
    }

    try {
      const [taskItems, profileItems] = await Promise.all([
        getJson<TaskSummary[]>("/v2/tasks").then(async (items) =>
          Promise.all(items.map((item) => getJson<TaskSummary>(`/v2/tasks/${item.id}`)))
        ),
        getJson<EnvProfile[]>("/v2/env-profiles")
      ]);

      setTasks(taskItems);
      setProfiles(profileItems);
      onStatsChange({ taskCount: taskItems.length, profileCount: profileItems.length });

      if (!envProfileId && profileItems[0]) {
        setEnvProfileId(profileItems[0].id);
      }

      const nextTask = pickPreferredTask(taskItems, options?.preferredTaskId, selectedTask?.id);
      setSelectedTask(nextTask);
      return true;
    } catch (error) {
      if (options?.errorScope === "create") {
        setCreateErrorMessage(getErrorMessage(error));
      } else {
        setPageErrorMessage(getErrorMessage(error));
      }
      return false;
    } finally {
      setIsRefreshing(false);
    }
  }

  useEffect(() => {
    void refresh({ errorScope: "page" });
  }, []);

  useEffect(() => {
    if (!successMessage) {
      clearSuccessTimer();
      return;
    }
    clearSuccessTimer();
    successTimeoutRef.current = window.setTimeout(() => {
      setSuccessMessage("");
      successTimeoutRef.current = null;
    }, 4000);
    return () => {
      clearSuccessTimer();
    };
  }, [successMessage]);

  useEffect(() => {
    return () => {
      clearSuccessTimer();
    };
  }, []);

  function handleOpenCreateModal() {
    clearSuccessTimer();
    setSuccessMessage("");
    setCreateErrorMessage("");
    setIsCreateModalOpen(true);
  }

  async function handleSubmitCreateTask() {
    if (!prompt.trim() || !envProfileId) {
      return;
    }
    setIsSubmitting(true);
    clearSuccessTimer();
    setSuccessMessage("");
    setCreateErrorMessage("");

    try {
      const task = await postJson<TaskSummary>("/v2/tasks", {
        prompt,
        env_profile_id: envProfileId,
        title: "",
        model_overrides: Object.fromEntries(Object.entries(modelOverrides).filter(([, value]) => value.trim()))
      });
      const refreshed = await refresh({ preferredTaskId: task.id, errorScope: "create" });
      if (!refreshed) {
        return;
      }
      setIsCreateModalOpen(false);
      setPrompt("");
      setModelOverrides({ review: "", test: "", report: "", capability_generation: "" });
      setSuccessMessage("任务创建成功，已加入任务中心。");
    } catch (error) {
      setCreateErrorMessage(getErrorMessage(error));
      setSuccessMessage("");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleSelectTask(taskId: string): boolean {
    const matched = tasks.find((item) => item.id === taskId) || null;
    setSelectedTask(matched);
    return Boolean(matched);
  }

  return (
    <section className="page-section tasks-layout">
      <section className="task-command-bar">
        <div className="task-command-bar__copy">
          <strong>{meta.title}</strong>
          <p>{meta.description}</p>
        </div>
        <div className="task-command-bar__actions">
          <button className="btn btn--primary" type="button" onClick={handleOpenCreateModal}>
            新建任务
          </button>
        </div>
      </section>
      {successMessage ? <div className="task-success-banner">{successMessage}</div> : null}
      {pageErrorMessage ? <div className="error-banner">{pageErrorMessage}</div> : null}
      <MetricStrip items={buildTaskMetrics(tasks, profiles, selectedTask)} />
      <div className="tasks-console-grid">
        <div ref={queueSectionRef} className="tasks-console-grid__queue">
          <TaskActionInbox
            tasks={tasks}
            selectedTaskId={selectedTask?.id || ""}
            onSelectTask={handleSelectTask}
            onAfterSelect={() => {
              queueSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
          />
          <TaskQueue
            tasks={tasks}
            selectedTaskId={selectedTask?.id || ""}
            isRefreshing={isRefreshing}
            onSelect={(taskId) => {
              handleSelectTask(taskId);
            }}
            onNavigateRuns={(context) => onNavigate("runs", context)}
          />
        </div>
        <div className="tasks-console-grid__inspector">
          <TaskInspector
            task={selectedTask}
            onNavigateRuns={(context) => onNavigate("runs", context)}
            onNavigateArtifacts={(context) => onNavigate("artifacts", context)}
            onNavigateCapabilities={() => onNavigate("capabilities")}
            onRefresh={async () => {
              await refresh({ preferredTaskId: selectedTask?.id, errorScope: "page" });
            }}
          />
        </div>
      </div>
      <TaskQuickCreateModal
        open={isCreateModalOpen}
        profiles={profiles}
        prompt={prompt}
        envProfileId={envProfileId}
        modelOverrides={modelOverrides}
        isSubmitting={isSubmitting}
        errorMessage={createErrorMessage}
        successMessage={successMessage}
        onPromptChange={setPrompt}
        onEnvProfileChange={setEnvProfileId}
        onModelOverridesChange={setModelOverrides}
        onClose={() => setIsCreateModalOpen(false)}
        onNavigateProfiles={() => {
          setIsCreateModalOpen(false);
          onNavigate("profiles");
        }}
        onSubmit={() => void handleSubmitCreateTask()}
      />
    </section>
  );
}
