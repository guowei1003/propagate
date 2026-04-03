import { useEffect, useState } from "react";

import { MetricStrip } from "../components/MetricStrip";
import { PageHeader } from "../components/PageHeader";
import { DependencyList } from "../components/runs/DependencyList";
import { EventStream } from "../components/runs/EventStream";
import { RunSummary } from "../components/runs/RunSummary";
import { SubtaskBoard } from "../components/runs/SubtaskBoard";
import { EmptyState } from "../components/EmptyState";
import { StatusBadge } from "../components/StatusBadge";
import { getErrorMessage, getJson, postJson } from "../lib/api";
import { subscribeRunEvents } from "../lib/events";
import { buildRunMetrics, getTaskStatusMeta } from "../lib/presenters";

type RunEvent = {
  id: string;
  event_type: string;
  message: string;
};

type TaskDetails = {
  id: string;
  title: string;
  run?: { id: string; status: string; current_phase: string } | null;
  env_profile?: { name: string; provider_type: string; default_model: string } | null;
  dependencies?: Array<{ from_sub_task_id: string; to_sub_task_id: string }>;
  subtasks?: Array<{ id: string; name: string; status: string; output_summary?: { selected_model?: string } }>;
  events?: RunEvent[];
};

type Props = {
  meta: {
    eyebrow: string;
    title: string;
    description: string;
  };
  onStatsChange: (update: { taskCount?: number; profileCount?: number; pendingCapabilities?: number }) => void;
};

export function RunsPage({ meta, onStatsChange }: Props) {
  const [items, setItems] = useState<TaskDetails[]>([]);
  const [activeRunId, setActiveRunId] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isResuming, setIsResuming] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [latestEventId, setLatestEventId] = useState("");

  async function refresh(preferredRunId?: string) {
    setIsRefreshing(true);
    setErrorMessage("");

    try {
      const tasks = await getJson<TaskDetails[]>("/v2/tasks");
      const detailed = await Promise.all(tasks.map((item) => getJson<TaskDetails>(`/v2/tasks/${item.id}`)));
      const availableRunIds = detailed.flatMap((item) => (item.run?.id ? [item.run.id] : []));
      const nextRunId =
        (preferredRunId && availableRunIds.includes(preferredRunId) && preferredRunId) ||
        (activeRunId && availableRunIds.includes(activeRunId) && activeRunId) ||
        availableRunIds[0] ||
        "";
      setItems(detailed);
      setActiveRunId(nextRunId);
      onStatsChange({ taskCount: detailed.length });
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
    if (!activeRunId) return;
    return subscribeRunEvents(activeRunId, (payload) => {
      setLatestEventId(payload.id);
      setItems((current) =>
        current.map((item) => {
          if (item.run?.id !== activeRunId) return item;
          return { ...item, events: [...(item.events || []), payload as RunEvent] };
        })
      );
    });
  }, [activeRunId]);

  async function handleResume(runId: string) {
    setIsResuming(true);
    setErrorMessage("");
    try {
      await postJson(`/v2/runs/${runId}/resume`, {});
      await refresh(runId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsResuming(false);
    }
  }

  const runnableItems = items.filter((item) => item.run?.id);
  const activeItem = runnableItems.find((item) => item.run?.id === activeRunId) || runnableItems[0] || null;
  const activeRunStatus = getTaskStatusMeta(activeItem?.run?.status || "");

  return (
    <section className="page-section">
      <PageHeader
        eyebrow={meta.eyebrow}
        title={meta.title}
        description={meta.description}
        actions={activeItem ? <StatusBadge label={`当前订阅：${activeRunStatus.label}`} tone={activeRunStatus.tone} /> : undefined}
      />
      {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}
      <MetricStrip items={buildRunMetrics(items, activeItem)} />
      {!activeItem ? (
        <EmptyState
          title="还没有可监控的运行"
          description="当任务进入运行阶段后，这里会显示运行摘要、依赖关系和实时事件流。"
          aside={isRefreshing ? "正在检查运行状态" : "等待任务进入运行阶段"}
        />
      ) : (
        <div className="workspace-grid">
          <div className="primary-column">
            <RunSummary
              item={activeItem}
              runOptions={runnableItems.map((item) => ({ id: item.run!.id, title: item.title || item.run!.id }))}
              activeRunId={activeItem.run?.id || ""}
              isResuming={isResuming}
              onSelectRun={setActiveRunId}
              onSubscribe={() => setActiveRunId(activeItem.run!.id)}
              onResume={() => void handleResume(activeItem.run!.id)}
            />
            <SubtaskBoard subtasks={activeItem.subtasks || []} />
            <DependencyList dependencies={activeItem.dependencies || []} subtasks={activeItem.subtasks || []} />
          </div>
          <div className="inspector-column">
            <EventStream events={activeItem.events || []} highlightId={latestEventId} />
          </div>
        </div>
      )}
    </section>
  );
}
