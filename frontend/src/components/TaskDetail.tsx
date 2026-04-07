import { useState, useEffect, useCallback, useRef } from "react";
import { getJson } from "../lib/api";
import { getTaskStatusMeta, formatRelativeTime, formatDuration } from "../presenters";
import { StatusBadge } from "./StatusBadge";

type TaskEvent = {
  id: number;
  event_type: string;
  message: string | null;
  payload: Record<string, unknown> | null;
  created_at: string;
};

type Task = {
  id: string;
  title: string;
  prompt: string;
  status: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  logs: TaskEvent[];
  result: {
    id: number;
    output: string | null;
    artifacts: Record<string, unknown> | null;
    created_at: string;
  } | null;
};

type Props = {
  taskId: string;
  onBack: () => void;
};

type Tab = "overview" | "logs" | "result";

const EVENT_TYPE_LABELS: Record<string, string> = {
  status_changed: "状态变更",
  phase: "阶段",
  llm_output: "LLM 输出",
  execution_result: "执行结果",
  error: "错误"
};

export function TaskDetail({ taskId, onBack }: Props) {
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("overview");
  const [eventSource, setEventSource] = useState<EventSource | null>(null);
  const [liveLogs, setLiveLogs] = useState<TaskEvent[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const loadTask = useCallback(async () => {
    try {
      const data = await getJson<Task>(`/api/tasks/${taskId}`);
      setTask(data);
      setLiveLogs(data.logs || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    loadTask();
    const es = new EventSource(`/api/tasks/${taskId}/stream`);
    setEventSource(es);

    es.addEventListener("status_changed", (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setLiveLogs((prev) => [
        ...prev,
        { id: Date.now(), event_type: "status_changed", message: data.message, payload: data.payload, created_at: new Date().toISOString() }
      ]);
      loadTask();
    });
    es.addEventListener("phase", (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setLiveLogs((prev) => [
        ...prev,
        { id: Date.now(), event_type: "phase", message: data.message, payload: data.payload, created_at: new Date().toISOString() }
      ]);
    });
    es.addEventListener("llm_output", (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setLiveLogs((prev) => [
        ...prev,
        { id: Date.now(), event_type: "llm_output", message: data.message, payload: data.payload, created_at: new Date().toISOString() }
      ]);
    });
    es.addEventListener("execution_result", (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setLiveLogs((prev) => [
        ...prev,
        { id: Date.now(), event_type: "execution_result", message: data.message, payload: data.payload, created_at: new Date().toISOString() }
      ]);
    });
    es.addEventListener("error", (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setLiveLogs((prev) => [
        ...prev,
        { id: Date.now(), event_type: "error", message: data.message, payload: data.payload, created_at: new Date().toISOString() }
      ]);
    });

    return () => {
      es.close();
    };
  }, [taskId, loadTask]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [liveLogs]);

  if (loading) {
    return (
      <div className="page-section">
        <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-muted)" }}>加载中...</div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="page-section">
        <div className="empty-state">
          <h3>任务不存在</h3>
          <button className="btn btn--ghost" onClick={onBack}>返回列表</button>
        </div>
      </div>
    );
  }

  const meta = getTaskStatusMeta(task.status);

  return (
    <div className="page-section">
      {/* Back button + header */}
      <div className="page-header">
        <div className="page-header__copy">
          <button className="btn btn--ghost" onClick={onBack} style={{ marginBottom: "8px" }}>
            ← 返回
          </button>
          <h2>{task.title}</h2>
          <p style={{ color: "var(--text-secondary)", marginTop: "4px" }}>{task.prompt}</p>
        </div>
        <StatusBadge label={meta.label} tone={meta.tone} />
      </div>

      {/* Tabs */}
      <div className="panel-frame" style={{ padding: "0", overflow: "hidden" }}>
        <div style={{ display: "flex", borderBottom: "1px solid var(--line-subtle)" }}>
          {(["overview", "logs", "result"] as Tab[]).map((t) => (
            <button
              key={t}
              className="btn"
              style={{
                borderRadius: "0",
                border: "none",
                borderBottom: tab === t ? "2px solid var(--accent-primary)" : "2px solid transparent",
                background: "transparent",
                minHeight: "52px"
              }}
              onClick={() => setTab(t)}
            >
              {t === "overview" ? "概览" : t === "logs" ? "日志" : "产物"}
              {t === "logs" && liveLogs.length > 0 && (
                <span style={{
                  marginLeft: "6px",
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "20px",
                  height: "20px",
                  borderRadius: "999px",
                  background: "var(--accent-info-soft)",
                  color: "var(--accent-primary)",
                  fontSize: "11px"
                }}>
                  {liveLogs.length}
                </span>
              )}
            </button>
          ))}
        </div>

        <div style={{ padding: "var(--space-6)" }}>
          {tab === "overview" && (
            <div className="stack">
              <dl className="key-value-grid key-value-grid--2">
                <div className="key-value-row">
                  <dt>任务 ID</dt>
                  <dd style={{ fontFamily: "var(--font-mono)", fontSize: "12px" }}>{task.id}</dd>
                </div>
                <div className="key-value-row">
                  <dt>创建时间</dt>
                  <dd>{new Date(task.created_at).toLocaleString("zh-CN")}</dd>
                </div>
                <div className="key-value-row">
                  <dt>更新时间</dt>
                  <dd>{new Date(task.updated_at).toLocaleString("zh-CN")}</dd>
                </div>
                <div className="key-value-row">
                  <dt>执行耗时</dt>
                  <dd>{formatDuration(task.created_at, task.completed_at)}</dd>
                </div>
                <div className="key-value-row" style={{ gridColumn: "1 / -1" }}>
                  <dt>任务描述</dt>
                  <dd style={{ whiteSpace: "pre-wrap" }}>{task.prompt}</dd>
                </div>
              </dl>
            </div>
          )}

          {tab === "logs" && (
            <div className="timeline-feed">
              {liveLogs.length === 0 ? (
                <div className="timeline-feed--empty">
                  <p>暂无日志，等待任务开始...</p>
                </div>
              ) : (
                liveLogs.map((log, i) => (
                  <div key={log.id} className={`timeline-item ${i === liveLogs.length - 1 ? "is-fresh" : ""}`}>
                    <div className="timeline-item__marker" />
                    <div className="timeline-item__body">
                      <div className="timeline-item__topline">
                        <span>{EVENT_TYPE_LABELS[log.event_type] || log.event_type}</span>
                        <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                          {formatRelativeTime(log.created_at)}
                        </span>
                      </div>
                      <p>{log.message || "(无消息)"}</p>
                      {log.payload && Object.keys(log.payload).length > 0 && (
                        <pre style={{
                          marginTop: "8px",
                          fontSize: "12px",
                          padding: "8px",
                          borderRadius: "var(--radius-sm)",
                          background: "var(--bg-elevated)",
                          overflow: "auto"
                        }}>
                          {JSON.stringify(log.payload, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          )}

          {tab === "result" && (
            <div className="stack">
              {task.result?.output ? (
                <div className="panel-frame">
                  <div className="panel-frame__header">
                    <span className="panel-frame__title">执行输出</span>
                  </div>
                  <pre style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "13px",
                    padding: "16px",
                    borderRadius: "var(--radius-md)",
                    background: "var(--bg-panel-muted)",
                    border: "1px solid var(--line-subtle)",
                    overflow: "auto",
                    maxHeight: "500px",
                    whiteSpace: "pre-wrap"
                  }}>
                    {task.result.output}
                  </pre>
                </div>
              ) : (
                <div className="empty-state">
                  <h3>暂无产物</h3>
                  <p>任务完成后将显示执行输出</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
