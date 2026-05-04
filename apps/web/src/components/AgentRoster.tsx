type Props = {
  agents: Array<Record<string, unknown>>;
};

export function AgentRoster({ agents }: Props) {
  return (
    <section className="card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Selected Agents</p>
          <h3>自动选配团队</h3>
        </div>
      </div>
      <div className="agent-grid">
        {agents.map((agent) => (
          <article className="agent-card" key={String(agent.id ?? agent.agent_id)}>
            <div className="agent-card__header">
              <div>
                <h4>{String(agent.name ?? agent.agent_id)}</h4>
                <p>{String(agent.role ?? "")}</p>
              </div>
              <span className="pill">{String(agent.model_tier ?? "runtime")}</span>
            </div>
            <div className="tag-row">
              {((agent.capabilities as string[]) ?? []).map((capability) => (
                <span className="tag" key={capability}>
                  {capability}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
