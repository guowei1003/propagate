import type { ReactNode } from "react";

type Props = {
  title: string;
  description?: string;
  actions?: ReactNode;
  tone?: "default" | "accent" | "warning";
  className?: string;
  children: ReactNode;
};

export function PanelFrame({ title, description, actions, tone = "default", className, children }: Props) {
  const classes = ["panel-frame", `panel-frame--${tone}`, className].filter(Boolean).join(" ");

  return (
    <section className={classes}>
      <header className="panel-frame__header">
        <div>
          <h3 className="panel-frame__title">{title}</h3>
          {description ? <p className="panel-frame__description">{description}</p> : null}
        </div>
        {actions ? <div className="panel-frame__actions">{actions}</div> : null}
      </header>
      <div className="panel-frame__body">{children}</div>
    </section>
  );
}
