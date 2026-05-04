import { FormEvent, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Profile } from "../lib/types";

export function ProfilesPage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [name, setName] = useState("default-mock");

  async function loadProfiles() {
    setProfiles(await api.listProfiles());
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    await api.createProfile({
      name,
      model_provider: "mock",
      model_name: "gpt-4.1-mini",
      temperature: 0.1,
      max_tokens: 4000,
      http_allowlist_domains: [],
      http_allowlist_methods: ["GET", "POST"],
      sandbox_cpu_limit: 1,
      sandbox_memory_limit_mb: 512,
      step_timeout_sec: 180,
      requires_human_approval_for_high_risk: true,
    });
    setName("default-mock");
    await loadProfiles();
  }

  useEffect(() => {
    void loadProfiles();
  }, []);

  return (
    <div className="page-grid">
      <form className="card" onSubmit={handleSubmit}>
        <div className="section-heading">
          <div>
            <p className="eyebrow">Profile</p>
            <h3>新建运行策略</h3>
          </div>
        </div>
        <label>
          <span>名称</span>
          <input value={name} onChange={(event) => setName(event.target.value)} />
        </label>
        <button className="button button--primary" type="submit">
          创建 Profile
        </button>
      </form>
      <section className="card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Profiles</p>
            <h3>已注册环境</h3>
          </div>
        </div>
        <div className="stack">
          {profiles.map((profile) => (
            <article key={profile.id} className="profile-card">
              <strong>{profile.name}</strong>
              <p>
                {profile.model_provider} / {profile.model_name}
              </p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
