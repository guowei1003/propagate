import type { ReactNode } from "react";
import { ThemeToggle } from "./ThemeToggle";

type Props = {
  children: ReactNode;
};

export function Layout({ children }: Props) {
  return (
    <div className="app-shell">
      <aside className="sidebar-rail">
        <div className="sidebar-section">
          <div>
            <p className="brand-title">Propagate</p>
            <p className="brand-summary" style={{ marginTop: "6px", fontSize: "13px", color: "var(--text-muted)" }}>
              AI Task Execution
            </p>
          </div>
        </div>

        <nav className="sidebar-nav">
          <a href="#/tasks" className="sidebar-nav-button is-active">
            <div className="sidebar-nav-button__topline">
              <span className="sidebar-nav-button__label">任务</span>
            </div>
            <span className="sidebar-nav-button__hint">任务管理与执行</span>
          </a>
          <a href="#/profiles" className="sidebar-nav-button">
            <div className="sidebar-nav-button__topline">
              <span className="sidebar-nav-button__label">环境</span>
            </div>
            <span className="sidebar-nav-button__hint">LLM 环境配置</span>
          </a>
        </nav>
      </aside>

      <div className="workspace-shell">
        <header className="console-topbar">
          <div className="console-topbar__copy">
            <span className="console-topbar__eyebrow">Propagate</span>
            <p className="console-topbar__description">AI 任务执行系统</p>
          </div>
          <div className="console-topbar__actions">
            <ThemeToggle />
          </div>
        </header>

        <main className="workspace workspace-transition">
          {children}
        </main>
      </div>
    </div>
  );
}
