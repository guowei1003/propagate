import { useEffect, useState } from "react";

import { MetricStrip } from "../components/MetricStrip";
import { PageHeader } from "../components/PageHeader";
import { TaskComposer } from "../components/tasks/TaskComposer";
import { TaskInspector } from "../components/tasks/TaskInspector";
import { TaskQueue } from "../components/tasks/TaskQueue";
import { getErrorMessage, getJson, postJson } from "../lib/api";
import { buildTaskMetrics } from "../lib/presenters";

type EnvProfile = { id: string; name: string };
type TaskSummary = {
  id: string;
  title: string;
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
  onNavigate: (view: "tasks" | "runs" | "capabilities" | "profiles" | "artifacts") => void;
  onStatsChange: (update: { taskCount?: number; profileCount?: number; pendingCapabilities?: number }) => void;
};

export function TasksPage({ meta, onNavigate, onStatsChange }: Props) {
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
  const [errorMessage, setErrorMessage] = useState("");

  async function refresh(preferredTaskId?: string) {
    setIsRefreshing(true);
    setErrorMessage("");

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

      const nextTask =
        taskItems.find((item) => item.id === preferredTaskId) ||
        taskItems.find((item) => item.id === selectedTask?.id) ||
        taskItems[0] ||
        null;

      setSelectedTask(nextTask);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsRefreshing(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleSubmit() {
    setIsSubmitting(true);
    setErrorMessage("");

    try {
      const task = await postJson<TaskSummary>("/v2/tasks", {
        prompt,
        env_profile_id: envProfileId,
        title: "",
        model_overrides: Object.fromEntries(Object.entries(modelOverrides).filter(([, value]) => value.trim()))
      });
      setPrompt("");
      setModelOverrides({ review: "", test: "", report: "", capability_generation: "" });
      await refresh(task.id);
      const detail = await getJson<TaskSummary>(`/v2/tasks/${task.id}`);
      setSelectedTask(detail);
      if (detail.status !== "WAITING_USER_INPUT") {
        onNavigate("runs");
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="page-section tasks-layout">
      <PageHeader eyebrow={meta.eyebrow} title={meta.title} description={meta.description} />
      {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}
      <MetricStrip items={buildTaskMetrics(tasks, profiles, selectedTask)} />
      <div className="tasks-console-grid">
        <div className="tasks-console-grid__composer">
          <TaskComposer
            profiles={profiles}
            prompt={prompt}
            envProfileId={envProfileId}
            modelOverrides={modelOverrides}
            isSubmitting={isSubmitting}
            onPromptChange={setPrompt}
            onEnvProfileChange={setEnvProfileId}
            onModelOverridesChange={setModelOverrides}
            onNavigateProfiles={() => onNavigate("profiles")}
            onSubmit={() => void handleSubmit()}
          />
        </div>
        <div className="tasks-console-grid__queue">
          <TaskQueue
            tasks={tasks}
            selectedTaskId={selectedTask?.id || ""}
            isRefreshing={isRefreshing}
            onSelect={(taskId) => setSelectedTask(tasks.find((item) => item.id === taskId) || null)}
            onNavigateRuns={() => onNavigate("runs")}
          />
        </div>
        <div className="tasks-console-grid__inspector">
          <TaskInspector
            task={selectedTask}
            onNavigateRuns={() => onNavigate("runs")}
            onRefresh={async () => {
              await refresh(selectedTask?.id);
            }}
          />
        </div>
      </div>
    </section>
  );
}
