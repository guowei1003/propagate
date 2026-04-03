import { FormEvent, useEffect, useState } from "react";

import { getJson, postJson, putJson } from "../lib/api";

type EnvProfile = {
  id: string;
  name: string;
  provider_type: string;
  api_base_url: string;
  default_model: string;
  review_model: string;
  test_model: string;
  capability_generation_model: string;
  report_model: string;
  temperature: number;
  default_timeout_sec: number;
  max_retries: number;
  max_concurrency: number;
  enable_docker_sandbox: boolean;
  enable_auto_sub_agents: boolean;
  api_key_masked: string;
};

const initialForm = {
  name: "",
  provider_type: "demo",
  api_base_url: "",
  api_key: "",
  default_model: "demo-heuristic",
  review_model: "",
  test_model: "",
  capability_generation_model: "",
  report_model: "",
  temperature: 0.2,
  default_timeout_sec: 300,
  max_retries: 2,
  max_concurrency: 2,
  enable_docker_sandbox: true,
  enable_auto_sub_agents: true
};

export function EnvProfilesPage() {
  const [items, setItems] = useState<EnvProfile[]>([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState("");
  const [validationMessageById, setValidationMessageById] = useState<Record<string, string>>({});

  async function refresh() {
    setItems(await getJson<EnvProfile[]>("/v2/env-profiles"));
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (editingId) {
      await putJson(`/v2/env-profiles/${editingId}`, form);
    } else {
      await postJson("/v2/env-profiles", form);
    }
    setForm(initialForm);
    setEditingId("");
    await refresh();
  }

  async function handleValidate(id: string) {
    const result = await postJson<{ message: string }>(`/v2/env-profiles/${id}/validate`, {});
    setValidationMessageById((current) => ({ ...current, [id]: result.message }));
  }

  async function handleEdit(id: string) {
    const detail = await getJson<EnvProfile>(`/v2/env-profiles/${id}`);
    setEditingId(id);
    setForm({
      name: detail.name,
      provider_type: detail.provider_type,
      api_base_url: detail.api_base_url,
      api_key: "",
      default_model: detail.default_model,
      review_model: detail.review_model,
      test_model: detail.test_model,
      capability_generation_model: detail.capability_generation_model,
      report_model: detail.report_model,
      temperature: detail.temperature,
      default_timeout_sec: detail.default_timeout_sec,
      max_retries: detail.max_retries,
      max_concurrency: detail.max_concurrency,
      enable_docker_sandbox: detail.enable_docker_sandbox,
      enable_auto_sub_agents: detail.enable_auto_sub_agents
    });
  }

  return (
    <section className="panel-grid">
      <article className="panel">
        <h2>{editingId ? "编辑环境配置" : "新增环境配置"}</h2>
        <form className="form" onSubmit={(event) => void handleSubmit(event)}>
          <label>
            名称
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
          </label>
          <label>
            Provider
            <select value={form.provider_type} onChange={(event) => setForm({ ...form, provider_type: event.target.value })}>
              <option value="demo">demo</option>
              <option value="openai_compatible">openai_compatible</option>
            </select>
          </label>
          <label>
            Default Model
            <input value={form.default_model} onChange={(event) => setForm({ ...form, default_model: event.target.value })} />
          </label>
          <label>
            API Base URL
            <input value={form.api_base_url} onChange={(event) => setForm({ ...form, api_base_url: event.target.value })} />
          </label>
          <label>
            API Key
            <input value={form.api_key} onChange={(event) => setForm({ ...form, api_key: event.target.value })} />
          </label>
          <label>
            Temperature
            <input type="number" step="0.1" value={form.temperature} onChange={(event) => setForm({ ...form, temperature: Number(event.target.value) })} />
          </label>
          <label>
            Default Timeout
            <input type="number" value={form.default_timeout_sec} onChange={(event) => setForm({ ...form, default_timeout_sec: Number(event.target.value) })} />
          </label>
          <label>
            Max Retries
            <input type="number" value={form.max_retries} onChange={(event) => setForm({ ...form, max_retries: Number(event.target.value) })} />
          </label>
          <label>
            Max Concurrency
            <input type="number" value={form.max_concurrency} onChange={(event) => setForm({ ...form, max_concurrency: Number(event.target.value) })} />
          </label>
          <label>
            Docker Sandbox
            <input type="checkbox" checked={form.enable_docker_sandbox} onChange={(event) => setForm({ ...form, enable_docker_sandbox: event.target.checked })} />
          </label>
          <label>
            Auto Sub Agents
            <input type="checkbox" checked={form.enable_auto_sub_agents} onChange={(event) => setForm({ ...form, enable_auto_sub_agents: event.target.checked })} />
          </label>
          <button type="submit">保存配置</button>
        </form>
      </article>
      <article className="panel">
        <h2>已配置环境</h2>
        <div className="stack">
          {items.map((item) => (
            <div key={item.id} className="card">
              <strong>{item.name}</strong>
              <span>{item.provider_type}</span>
              <span>default: {item.default_model}</span>
              <span>review: {item.review_model || "-"}</span>
              <span>test: {item.test_model || "-"}</span>
              <span>capability: {item.capability_generation_model || "-"}</span>
              <span>report: {item.report_model || "-"}</span>
              <span>timeout: {item.default_timeout_sec}</span>
              <span>retries: {item.max_retries}</span>
              <span>concurrency: {item.max_concurrency}</span>
              <span>key: {item.api_key_masked || "-"}</span>
              <div className="actions">
                <button
                  type="button"
                  onClick={() => void handleEdit(item.id)}
                >
                  编辑
                </button>
                <button type="button" onClick={() => void handleValidate(item.id)}>
                  校验
                </button>
              </div>
              {validationMessageById[item.id] && <p>{validationMessageById[item.id]}</p>}
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}
