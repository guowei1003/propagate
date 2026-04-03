import type { MetricItem } from "../lib/presenters";

type Props = {
  items: MetricItem[];
};

export function MetricStrip({ items }: Props) {
  return (
    <section className="metric-strip" aria-label="关键指标">
      {items.map((item) => (
        <article key={item.label} className={`metric-card metric-card--${item.tone}`}>
          <span className="metric-card__label">{item.label}</span>
          <strong className="metric-card__value">{item.value}</strong>
          <span className="metric-card__detail">{item.detail}</span>
        </article>
      ))}
    </section>
  );
}
