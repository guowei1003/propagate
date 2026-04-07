import { useState, useEffect } from "react";
import { getJson, postJson, putJson, deleteJson } from "../lib/api";
import { useToast } from "../lib/toast";
import { MetricStrip } from "./MetricStrip";

type Profile = {
  id: string;
  name: string;
  llm_model: string;
  temperature: number;
  timeout_sec: number;
  created_at: string;
};

export function ProfilesPage() {
  const { pushToast } = useToast();
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", llm_model: "demo-heuristic", temperature: 0.2, timeout_sec: 300 });
  const [saving, setSaving] = useState(false);

  const loadProfiles = async () => {
    try {
      const data = await getJson<Profile[]>("/api/profiles");
      setProfiles(data);
    } catch {
      pushToast({ message: "加载环境配置失败", tone: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfiles();
  }, []);

  const handleSave = async () => {
    if (!form.name.trim()) {
      pushToast({ message: "请填写名称", tone: "warning" });
      return;
    }
    setSaving(true);
    try {
      if (editingId) {
        await putJson(`/api/profiles/${editingId}`, form);
        pushToast({ message: "配置已更新", tone: "success" });
      } else {
        await postJson("/api/profiles", form);
        pushToast({ message: "配置已创建", tone: "success" });
      }
      setEditingId(null);
      setForm({ name: "", llm_model: "demo-heuristic", temperature: 0.2, timeout_sec: 300 });
      loadProfiles();
    } catch (e) {
      pushToast({ message: `保存失败: ${e instanceof Error ? e.message : String(e)}`, tone: "error" });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteJson(`/api/profiles/${id}`);
      pushToast({ message: "配置已删除", tone: "success" });
      loadProfiles();
    } catch (e) {
      pushToast({ message: `删除失败: ${e instanceof Error ? e.message : String(e)}`, tone: "error" });
    }
  };

  const startEdit = (p: Profile) => {
    setEditingId(p.id);
    setForm({ name: p.name, llm_model: p.llm_model, temperature: p.temperature, timeout_sec: p.timeout_sec });
  };

  const metrics = profiles.length > 0
    ? profiles.map((p) => ({
        label: p.name,
        value: p.llm_model,
        detail: `Temperature ${p.temperature} / ${p.timeout_sec}s`,
        tone: (p.llm_model === "demo-heuristic" ? "neutral" : "info") as "neutral" | "info"
      }))
    : [{
        label: "环境数",
        value: String(profiles.length),
        detail: "当前配置的环境数",
        tone: ("neutral") as "neutral"
      }];

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-muted)" }}>
        加载中...
      </div>
    );
  }

  return (
    <div className="page-section">
      <MetricStrip items={metrics} />

      <div className="panel-frame">
        <div className="panel-frame__header">
          <div>
            <span className="panel-frame__title">{editingId ? "编辑环境" : "新建环境"}</span>
          </div>
        </div>

        <div className="form-group">
          <div className="field-inline">
            <div className="field">
              <label htmlFor="profile-name">名称</label>
              <input
                id="profile-name"
                className="input"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="例如：OpenAI GPT-4"
              />
            </div>
            <div className="field">
              <label htmlFor="profile-model">模型</label>
              <input
                id="profile-model"
                className="input"
                value={form.llm_model}
                onChange={(e) => setForm({ ...form, llm_model: e.target.value })}
                placeholder="gpt-4o-mini"
              />
            </div>
          </div>
          <div className="field-inline">
            <div className="field">
              <label htmlFor="profile-temp">Temperature</label>
              <input
                id="profile-temp"
                type="number"
                className="input"
                value={form.temperature}
                onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) })}
                step="0.1"
                min="0"
                max="2"
              />
            </div>
            <div className="field">
              <label htmlFor="profile-timeout">超时（秒）</label>
              <input
                id="profile-timeout"
                type="number"
                className="input"
                value={form.timeout_sec}
                onChange={(e) => setForm({ ...form, timeout_sec: parseInt(e.target.value) })}
                min="10"
                max="3600"
              />
            </div>
          </div>
        </div>

        <div className="panel-frame__actions" style={{ marginTop: "var(--space-4)" }}>
          <button className="btn btn--primary" onClick={handleSave} disabled={saving}>
            {saving ? "保存中..." : "保存"}
          </button>
          {editingId && (
            <button
              className="btn btn--ghost"
              onClick={() => {
                setEditingId(null);
                setForm({ name: "", llm_model: "demo-heuristic", temperature: 0.2, timeout_sec: 300 });
              }}
            >
              取消
            </button>
          )}
        </div>
      </div>

      {profiles.length === 0 ? (
        <div className="empty-state">
          <h3>暂无环境配置</h3>
          <p>在上方创建一个新的环境配置</p>
        </div>
      ) : (
        <div className="profile-list">
          {profiles.map((p) => (
            <div key={p.id} className="profile-card">
              <div className="profile-card__header">
                <div className="profile-card__title">
                  <strong>{p.name}</strong>
                  <div className="task-row__meta">
                    <span>模型: {p.llm_model}</span>
                    <span>Temperature: {p.temperature}</span>
                    <span>超时: {p.timeout_sec}s</span>
                  </div>
                </div>
                <div className="profile-card__actions">
                  <button className="btn btn--ghost" onClick={() => startEdit(p)}>编辑</button>
                  <button className="btn btn--danger" onClick={() => handleDelete(p.id)}>删除</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
