import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { AgentSpec } from "../lib/types";

export function AgentCatalogPage() {
  const [agents, setAgents] = useState<AgentSpec[]>([]);

  useEffect(() => {
    void api.listAgents().then(setAgents);
  }, []);

  return (
    <section className="card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Registry</p>
          <h3>内置智能体目录</h3>
        </div>
      </div>
      <div className="agent-grid">
        {agents.map((agent) => (
          <article key={agent.id} className="agent-card">
            <div className="agent-card__header">
              <div>
                <h4>{agent.name}</h4>
                <p>{agent.role}</p>
              </div>
              <span className="pill">{agent.model_tier}</span>
            </div>
            <div className="tag-row">
              {agent.capabilities.map((capability) => (
                <span className="tag" key={capability}>
                  {capability}
                </span>
              ))}
            </div>
            <p className="muted">
              tools: {agent.allowed_tools.join(", ") || "无"} · steps: {agent.allowed_step_kinds.join(", ") || "无"}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
