type TimelineItem = {
  id: string;
  title: string;
  description: string;
  meta: string;
};

type Props = {
  items: TimelineItem[];
  emptyTitle: string;
  emptyDescription: string;
  highlightId?: string;
};

export function TimelineFeed({ items, emptyTitle, emptyDescription, highlightId }: Props) {
  if (items.length === 0) {
    return (
      <div className="timeline-feed timeline-feed--empty">
        <h4>{emptyTitle}</h4>
        <p>{emptyDescription}</p>
      </div>
    );
  }

  return (
    <div className="timeline-feed">
      {items.map((item) => (
        <article
          key={item.id}
          className={item.id === highlightId ? "timeline-item is-fresh" : "timeline-item"}
        >
          <div className="timeline-item__marker" />
          <div className="timeline-item__body">
            <div className="timeline-item__topline">
              <strong>{item.title}</strong>
              <span>{item.meta}</span>
            </div>
            <p>{item.description}</p>
          </div>
        </article>
      ))}
    </div>
  );
}
