import { useEffect, useState } from "react";

import { ArtifactBundlePanel } from "../components/artifacts/ArtifactBundlePanel";
import { MetricStrip } from "../components/MetricStrip";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { getErrorMessage, getJson, postJson } from "../lib/api";
import { buildArtifactMetrics } from "../lib/presenters";

type TaskSummary = { id: string; title: string; run?: { id: string } | null };

type Props = {
  meta: {
    eyebrow: string;
    title: string;
    description: string;
  };
  onStatsChange: (update: { taskCount?: number; profileCount?: number; pendingCapabilities?: number }) => void;
  taskNavContext?: {
    taskId?: string;
    runId?: string;
    navigationVersion: number;
  };
};

function pickTaskForArtifacts(
  items: TaskSummary[],
  context?: {
    taskId?: string;
    runId?: string;
  }
): TaskSummary | null {
  if (context?.runId) {
    const matchedByRun = items.find((item) => item.run?.id === context.runId);
    if (matchedByRun) {
      return matchedByRun;
    }
  }
  if (context?.taskId) {
    const matchedByTask = items.find((item) => item.id === context.taskId && item.run?.id);
    if (matchedByTask) {
      return matchedByTask;
    }
  }
  return items.find((item) => item.run?.id) || null;
}

export function ArtifactsPage({ meta, onStatsChange, taskNavContext }: Props) {
  const [artifacts, setArtifacts] = useState<Record<string, unknown> | null>(null);
  const [runId, setRunId] = useState("");
  const [taskTitle, setTaskTitle] = useState("");
  const [isBuilding, setIsBuilding] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [contextNotice, setContextNotice] = useState("");

  async function refresh(context?: { taskId?: string; runId?: string }) {
    setIsRefreshing(true);
    setErrorMessage("");
    setContextNotice("");

    try {
      const items = await getJson<TaskSummary[]>("/v2/tasks");
      onStatsChange({ taskCount: items.length });
      const targetTask = pickTaskForArtifacts(items, context);
      const latestRunId = targetTask?.run?.id;
      if (!latestRunId) {
        if (context?.runId || context?.taskId) {
          setContextNotice("未找到该任务的可用交付产物，已清空当前展示。");
        }
        setRunId("");
        setTaskTitle("");
        setArtifacts(null);
        return;
      }

      setRunId(latestRunId);
      setTaskTitle(targetTask?.title || "");
      setArtifacts(await getJson<Record<string, unknown>>(`/v2/runs/${latestRunId}/artifacts`));
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsRefreshing(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    if (!taskNavContext?.navigationVersion) {
      return;
    }
    void refresh({
      taskId: taskNavContext.taskId,
      runId: taskNavContext.runId
    });
  }, [taskNavContext?.navigationVersion]);

  async function handleBuildBundle() {
    if (!runId) return;
    setIsBuilding(true);
    setErrorMessage("");
    try {
      await postJson(`/v2/runs/${runId}/bundle/build`, {});
      setArtifacts(await getJson<Record<string, unknown>>(`/v2/runs/${runId}/bundle`));
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsBuilding(false);
    }
  }

  return (
    <section className="page-section artifacts-layout">
      <PageHeader
        eyebrow={meta.eyebrow}
        title={meta.title}
        description={meta.description}
        actions={
          <StatusBadge
            label={runId ? (isBuilding ? "最近 Bundle：构建中" : "最近 Bundle：可操作") : "最近 Bundle：等待运行"}
            tone={runId ? (isBuilding ? "warning" : "info") : "neutral"}
          />
        }
      />
      {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}
      {contextNotice ? <div className="task-context-notice">{contextNotice}</div> : null}
      <MetricStrip items={buildArtifactMetrics({ runId, artifacts, isBuilding })} />
      <ArtifactBundlePanel
        runId={runId}
        taskTitle={taskTitle}
        artifacts={artifacts}
        isBuilding={isBuilding || isRefreshing}
        onBuild={() => void handleBuildBundle()}
      />
    </section>
  );
}
