import { useState, useEffect, useCallback } from "react";
import { getJson, postJson, deleteJson } from "../lib/api";
import { useToast } from "../lib/toast";
import { getTaskStatusMeta, buildTaskMetrics, formatRelativeTime } from "../presenters";
import { StatusBadge } from "./StatusBadge";
import { MetricStrip } from "./MetricStrip";

type Task = {
  id: string;
  title: string;
  status: string;
  prompt: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
};

type Props = {
  onSelectTask: (taskId: string) => void;
};

export function TaskList({ onSelectTask }: Props) {
  const { pushToast } = useToast();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [search, setSearch] = useState("");

  const loadTasks = useCallback(async () => {
    try {
      const data = await getJson<Task[]>("/api/tasks");
      setTasks(data);
    } catch {
      pushToast({ message: "加载任务列表失败", tone: "error" });
    } finally {
      setLoading(false);
    }
  }, [pushToast]);

  useEffect(() => {
    loadTasks();
    const interval = setInterval(loadTasks, 3000);
    return () => clearInterval(interval);
  }, [loadTasks]);

  const filtered = tasks.filter((t) => {
    const matchStatus = statusFilter === "ALL" || t.status === statusFilter;
    const matchSearch = search === "" || t.title.toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

  const metrics = buildTaskMetrics(tasks);

  if (loading) {
    return (
      <div className="page-section">
        <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-muted)" }}>
          加载中...
        </div>
      </div>
    );
  }

  return (
    <div className="page-section">
      <MetricStrip items={metrics} />

      <div className="task-command-bar">
        <div className="task-command-bar__copy">
          <input
            type="search"
            className="input"
            placeholder="搜索任务..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: "240px" }}
          />
        </div>
        <div className="task-command-bar__actions">
          {["ALL", "PENDING", "RUNNING", "COMPLETED", "FAILED"].map((s) => (
            <button
              key={s}
              className={`btn ${statusFilter === s ? "btn--primary" : "btn--ghost"}`}
              onClick={() => setStatusFilter(s)}
            >
              {s === "ALL" ? "全部" : getTaskStatusMeta(s).label}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">
          <h3>暂无任务</h3>
          <p>点击右上角「新建任务」创建一个任务</p>
        </div>
      ) : (
        <div className="task-list">
          {filtered.map((task) => {
            const meta = getTaskStatusMeta(task.status);
            return (
              <div
                key={task.id}
                className="task-row"
                onClick={() => onSelectTask(task.id)}
                style={{ cursor: "pointer" }}
              >
                <div className="task-row__header">
                  <div className="task-row__title">
                    <strong>{task.title}</strong>
                  </div>
                  <StatusBadge label={meta.label} tone={meta.tone} />
                </div>
                <div className="task-row__meta">
                  <span>{formatRelativeTime(task.created_at)}</span>
                  {task.completed_at && <span>耗时约 {formatRelativeTime(task.created_at)}</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
