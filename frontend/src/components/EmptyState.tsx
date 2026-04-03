import type { ReactNode } from "react";

type Props = {
  title: string;
  description: string;
  action?: ReactNode;
  aside?: string;
};

export function EmptyState({ title, description, action, aside }: Props) {
  return (
    <div className="empty-state">
      <p className="empty-state__eyebrow">空状态</p>
      <h3>{title}</h3>
      <p>{description}</p>
      {action ? <div className="empty-state__action">{action}</div> : null}
      {aside ? <span className="empty-state__aside">{aside}</span> : null}
    </div>
  );
}
