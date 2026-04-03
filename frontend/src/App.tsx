import { useEffect, useState } from "react";

import { ArtifactsPage } from "./pages/ArtifactsPage";
import { CapabilitiesPage } from "./pages/CapabilitiesPage";
import { EnvProfilesPage } from "./pages/EnvProfilesPage";
import { RunsPage } from "./pages/RunsPage";
import { TasksPage } from "./pages/TasksPage";

type ViewKey = "tasks" | "runs" | "capabilities" | "profiles" | "artifacts";

const views: Array<{ key: ViewKey; label: string }> = [
  { key: "tasks", label: "任务工作台" },
  { key: "runs", label: "运行监控" },
  { key: "capabilities", label: "能力中心" },
  { key: "profiles", label: "环境配置" },
  { key: "artifacts", label: "产物中心" }
];

export default function App() {
  const [view, setView] = useState<ViewKey>("tasks");

  useEffect(() => {
    const hash = window.location.hash.replace("#", "") as ViewKey;
    if (hash && views.some((item) => item.key === hash)) {
      setView(hash);
    }
  }, []);

  useEffect(() => {
    window.location.hash = view;
  }, [view]);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Propagate V2</p>
          <h1>AI Execution Console</h1>
          <p className="muted">任务、能力、环境配置和 bundle 审计统一收敛到一套工作台。</p>
        </div>
        <nav className="nav">
          {views.map((item) => (
            <button
              key={item.key}
              className={item.key === view ? "nav-item active" : "nav-item"}
              onClick={() => setView(item.key)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>
      <main className="content">
        {view === "tasks" && <TasksPage onNavigate={setView} />}
        {view === "runs" && <RunsPage />}
        {view === "capabilities" && <CapabilitiesPage />}
        {view === "profiles" && <EnvProfilesPage />}
        {view === "artifacts" && <ArtifactsPage />}
      </main>
    </div>
  );
}
