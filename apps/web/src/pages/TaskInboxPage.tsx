import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { TaskSummary } from "../lib/types";
import { StatusBadge } from "../components/StatusBadge";
import { TaskComposer } from "../components/TaskComposer";

export function TaskInboxPage() {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function loadTasks() {
    try {
      setTasks(await api.listTasks());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载任务失败");
    }
  }

  async function handleCreate(payload: {
    title: string;
    goal: string;
    constraints: string[];
    deliverables: string[];
    approval_mode: string;
  }) {
    const task = await api.createTask(payload);
    await loadTasks();
    if (task.latest_run?.id) {
      window.location.hash = `#/tasks/${task.id}/runs/${task.latest_run.id}`;
    }
  }

  useEffect(() => {
    void loadTasks();
  }, []);

  return (
    <div className="page-grid">
      <TaskComposer onSubmit={handleCreate} />
      <section className="card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Inbox</p>
            <h3>任务队列</h3>
          </div>
          <button className="button button--ghost" onClick={() => void loadTasks()}>
            刷新
          </button>
        </div>
        {error ? <p className="error">{error}</p> : null}
        <div className="task-list">
          {tasks.map((task) => (
            <button
              key={task.id}
              className="task-card"
              onClick={() => {
                if (task.latest_run_id) {
                  window.location.hash = `#/tasks/${task.id}/runs/${task.latest_run_id}`;
                }
              }}
            >
              <div className="task-card__head">
                <div>
                  <strong>{task.title}</strong>
                  <p>{task.goal}</p>
                </div>
                <StatusBadge status={task.latest_run_id ? "ready" : "draft"} />
              </div>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
