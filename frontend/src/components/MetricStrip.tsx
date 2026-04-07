import type { ReactNode } from "react";
import type { MetricItem } from "../presenters";
import type { Tone } from "../presenters";

type Props = {
  items: MetricItem[];
};

function MetricCard({ item }: { item: MetricItem }) {
  return (
    <div className={`metric-card metric-card--${item.tone}`}>
      <span className="metric-card__label">{item.label}</span>
      <strong className="metric-card__value">{item.value}</strong>
      <span className="metric-card__detail">{item.detail}</span>
    </div>
  );
}

export function MetricStrip({ items }: Props) {
  return (
    <div className="metric-strip">
      {items.map((item, i) => (
        <MetricCard key={i} item={item} />
      ))}
    </div>
  );
}
