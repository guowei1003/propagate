import { FormEvent, useEffect, useState } from "react";

import { getJson, postJson } from "../lib/api";
import { TaskDetailPage } from "./TaskDetailPage";

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
  onNavigate: (view: "tasks" | "runs" | "capabilities" | "profiles" | "artifacts") => void;
};

export function TasksPage({ onNavigate }: Props) {
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

  async function refresh() {
    const [taskItems, profileItems] = await Promise.all([
      getJson<TaskSummary[]>("/v2/tasks").then(async (items) => Promise.all(items.map((item) => getJson<TaskSummary>(`/v2/tasks/${item.id}`)))),
      getJson<EnvProfile[]>("/v2/env-profiles")
    ]);
    setTasks(taskItems);
    setProfiles(profileItems);
    if (!envProfileId && profileItems[0]) {
      setEnvProfileId(profileItems[0].id);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const task = await postJson<TaskSummary>("/v2/tasks", {
      prompt,
      env_profile_id: envProfileId,
      title: "",
      model_overrides: Object.fromEntries(Object.entries(modelOverrides).filter(([, value]) => value.trim()))
    });
    setPrompt("");
    setModelOverrides({ review: "", test: "", report: "", capability_generation: "" });
    await refresh();
    const detail = await getJson<TaskSummary>(`/v2/tasks/${task.id}`);
    setSelectedTask(detail);
    if (detail.status !== "WAITING_USER_INPUT") {
      onNavigate("runs");
    }
  }

  return (
    <section className="panel-grid">
      <article className="panel">
        <h2>创建任务</h2>
        <form className="form" onSubmit={(event) => void handleSubmit(event)}>
          <label>
            环境配置
            <select value={envProfileId} onChange={(event) => setEnvProfileId(event.target.value)}>
              {profiles.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            需求描述
            <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={8} />
          </label>
          <label>
            Review 模型覆盖
            <input value={modelOverrides.review} onChange={(event) => setModelOverrides({ ...modelOverrides, review: event.target.value })} />
          </label>
          <label>
            Test 模型覆盖
            <input value={modelOverrides.test} onChange={(event) => setModelOverrides({ ...modelOverrides, test: event.target.value })} />
          </label>
          <label>
            Report 模型覆盖
            <input value={modelOverrides.report} onChange={(event) => setModelOverrides({ ...modelOverrides, report: event.target.value })} />
          </label>
          <label>
            Capability 生成模型覆盖
            <input
              value={modelOverrides.capability_generation}
              onChange={(event) => setModelOverrides({ ...modelOverrides, capability_generation: event.target.value })}
            />
          </label>
          <button type="submit">创建任务</button>
        </form>
      </article>
      <article className="panel">
        <h2>最近任务</h2>
        <div className="stack">
          {tasks.map((item) => (
            <div key={item.id} className="card">
              <strong>{item.title}</strong>
              <span>{item.status}</span>
              <span>{item.current_phase}</span>
              <span>{item.env_profile?.name || "-"}</span>
              <div className="actions">
                <button type="button" onClick={() => setSelectedTask(item)}>
                  查看详情
                </button>
                <button type="button" onClick={() => onNavigate("runs")}>
                  查看运行
                </button>
              </div>
            </div>
          ))}
        </div>
      </article>
      {selectedTask && <TaskDetailPage task={selectedTask} onRefresh={async () => {
        const detail = await getJson<TaskSummary>(`/v2/tasks/${selectedTask.id}`);
        setSelectedTask(detail);
        await refresh();
      }} />}
    </section>
  );
}
