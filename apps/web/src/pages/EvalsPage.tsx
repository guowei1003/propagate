import { evalScenarios } from "../lib/evals";

export function EvalsPage() {
  return (
    <section className="card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Golden Tasks</p>
          <h3>评估覆盖场景</h3>
        </div>
      </div>
      <div className="eval-grid">
        {evalScenarios.map((scenario) => (
          <article key={scenario} className="eval-card">
            <strong>{scenario}</strong>
            <p className="muted">mock provider 与监督链路都应对该场景给出可回放结果。</p>
          </article>
        ))}
      </div>
    </section>
  );
}
