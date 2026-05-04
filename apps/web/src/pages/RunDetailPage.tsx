import { useEffect, useState } from "react";
import { AgentRoster } from "../components/AgentRoster";
import { ApprovalDrawer } from "../components/ApprovalDrawer";
import { ArtifactPanel } from "../components/ArtifactPanel";
import { EventTimeline } from "../components/EventTimeline";
import { MissionPanel } from "../components/MissionPanel";
import { PlanGraph } from "../components/PlanGraph";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../lib/api";
import type { RunDetail, RunEvent } from "../lib/types";

type Props = {
  taskId: string;
  runId: string;
};

export function RunDetailPage({ taskId, runId }: Props) {
  const [run, setRun] = useState<RunDetail | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const [runDetail, runEvents] = await Promise.all([
        api.getRun(taskId, runId),
        api.getRunEvents(taskId, runId),
      ]);
      setRun(runDetail);
      setEvents(runEvents);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载运行详情失败");
    }
  }

  async function handleApprove(approvalId: string) {
    await api.approveStep(taskId, runId, { approval_id: approvalId });
    await api.resumeRun(taskId, runId);
    await load();
  }

  async function handleReject(approvalId: string) {
    await api.rejectStep(taskId, runId, { approval_id: approvalId });
    await load();
  }

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 2500);
    return () => window.clearInterval(timer);
  }, [taskId, runId]);

  if (error) {
    return <p className="error">{error}</p>;
  }

  if (!run) {
    return <p className="muted">加载中...</p>;
  }

  return (
    <div className="stack">
      <section className="hero card">
        <div>
          <p className="eyebrow">Run</p>
          <h3>{run.thread_id}</h3>
          <p className="muted">任务 ID：{run.task_id}</p>
        </div>
        <div className="hero__meta">
          <StatusBadge status={run.status} />
          <button className="button button--ghost" onClick={() => void load()}>
            刷新
          </button>
        </div>
      </section>

      <MissionPanel mission={run.mission} />
      <div className="grid two">
        <PlanGraph steps={run.steps} />
        <AgentRoster agents={run.selected_agents} />
      </div>
      <div className="grid two">
        <ApprovalDrawer approvals={run.approvals} onApprove={handleApprove} onReject={handleReject} />
        <ArtifactPanel artifacts={run.artifacts} />
      </div>
      <section className="card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Verification</p>
            <h3>最终验证摘要</h3>
          </div>
        </div>
        <pre>{JSON.stringify(run.verification_summary, null, 2)}</pre>
      </section>
      <EventTimeline events={events} />
    </div>
  );
}
