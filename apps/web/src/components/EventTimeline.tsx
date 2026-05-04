import type { RunEvent } from "../lib/types";

type Props = {
  events: RunEvent[];
};

export function EventTimeline({ events }: Props) {
  return (
    <section className="card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Timeline</p>
          <h3>事件流</h3>
        </div>
      </div>
      <div className="timeline">
        {events.map((event) => (
          <article key={event.id} className="timeline-item">
            <div className="timeline-item__meta">
              <strong>#{event.sequence}</strong>
              <span>{event.category}</span>
            </div>
            <h4>{event.message}</h4>
            <pre>{JSON.stringify(event.payload, null, 2)}</pre>
          </article>
        ))}
      </div>
    </section>
  );
}
