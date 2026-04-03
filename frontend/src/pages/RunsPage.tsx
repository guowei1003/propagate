import { useEffect, useState } from "react";

import { getJson, postJson } from "../lib/api";
import { subscribeRunEvents } from "../lib/events";

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

export function RunsPage() {
  const [items, setItems] = useState<TaskDetails[]>([]);
  const [activeRunId, setActiveRunId] = useState("");

  useEffect(() => {
    void getJson<TaskDetails[]>("/v2/tasks").then(async (tasks) => {
      const detailed = await Promise.all(tasks.map((item) => getJson<TaskDetails>(`/v2/tasks/${item.id}`)));
      setItems(detailed);
      setActiveRunId(detailed.find((item) => item.run?.id)?.run?.id || "");
    });
  }, []);

  useEffect(() => {
    if (!activeRunId) return;
    return subscribeRunEvents(activeRunId, (payload) => {
      setItems((current) =>
        current.map((item) => {
          if (item.run?.id !== activeRunId) return item;
          return { ...item, events: [...(item.events || []), payload as RunEvent] };
        })
      );
    });
  }, [activeRunId]);

  async function handleResume(runId: string) {
    await postJson(`/v2/runs/${runId}/resume`, {});
    const tasks = await getJson<TaskDetails[]>("/v2/tasks");
    const detailed = await Promise.all(tasks.map((item) => getJson<TaskDetails>(`/v2/tasks/${item.id}`)));
    setItems(detailed);
  }

  return (
    <section className="panel">
      <h2>运行监控</h2>
      <div className="stack">
        {items.map((item) => (
          <div key={item.id} className="card">
            <strong>{item.title}</strong>
            <span>Run: {item.run?.id || "-"}</span>
            <span>Status: {item.run?.status || "-"}</span>
            <span>Phase: {item.run?.current_phase || "-"}</span>
            <span>Profile: {item.env_profile?.name || "-"}</span>
            <span>Default Model: {item.env_profile?.default_model || "-"}</span>
            <pre>{JSON.stringify(item.dependencies || [], null, 2)}</pre>
            <pre>{JSON.stringify(item.subtasks || [], null, 2)}</pre>
            <pre>{JSON.stringify(item.events || [], null, 2)}</pre>
            {item.run?.id && (
              <div className="actions">
                <button type="button" onClick={() => setActiveRunId(item.run!.id)}>
                  订阅事件
                </button>
                <button type="button" onClick={() => void handleResume(item.run!.id)}>
                  恢复执行
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
