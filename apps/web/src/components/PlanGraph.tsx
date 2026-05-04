import type { RunStep } from "../lib/types";
import { StatusBadge } from "./StatusBadge";

type Props = {
  steps: RunStep[];
};

export function PlanGraph({ steps }: Props) {
  return (
    <section className="card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Plan Graph</p>
          <h3>步骤 DAG</h3>
        </div>
      </div>
      <div className="step-list">
        {steps.map((step) => (
          <article key={step.id} className="step-card">
            <div className="step-card__head">
              <div>
                <strong>
                  {step.position + 1}. {step.title}
                </strong>
                <p>
                  {step.kind} · {step.assigned_agent_id}
                </p>
              </div>
              <StatusBadge status={step.status} />
            </div>
            <p className="muted">
              依赖：{step.dependencies.length > 0 ? step.dependencies.join(", ") : "无"} · 期望产物：
              {step.expected_artifacts.length > 0 ? step.expected_artifacts.join(", ") : "无"}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
