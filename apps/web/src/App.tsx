import { useEffect, useMemo, useState } from "react";
import { AgentCatalogPage } from "./pages/AgentCatalogPage";
import { EvalsPage } from "./pages/EvalsPage";
import { ProfilesPage } from "./pages/ProfilesPage";
import { RunDetailPage } from "./pages/RunDetailPage";
import { TaskInboxPage } from "./pages/TaskInboxPage";

type Route =
  | { page: "tasks" }
  | { page: "run"; taskId: string; runId: string }
  | { page: "profiles" }
  | { page: "agents" }
  | { page: "evals" };

function parseRoute(): Route {
  const hash = window.location.hash.replace(/^#/, "") || "/tasks";
  const parts = hash.split("/").filter(Boolean);
  if (parts[0] === "tasks" && parts[1] && parts[2] === "runs" && parts[3]) {
    return { page: "run", taskId: parts[1], runId: parts[3] };
  }
  if (parts[0] === "profiles") return { page: "profiles" };
  if (parts[0] === "agents") return { page: "agents" };
  if (parts[0] === "evals") return { page: "evals" };
  return { page: "tasks" };
}

export function App() {
  const [route, setRoute] = useState<Route>(parseRoute);

  useEffect(() => {
    const handler = () => setRoute(parseRoute());
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);

  const title = useMemo(() => {
    switch (route.page) {
      case "run":
        return "运行监督台";
      case "profiles":
        return "环境配置";
      case "agents":
        return "智能体目录";
      case "evals":
        return "评估场景";
      default:
        return "任务收件箱";
    }
  }, [route]);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand__eyebrow">Mission Harness</span>
          <h1>Propagate</h1>
          <p>目标、计划、监督、审批与验证都在同一个控制面里完成。</p>
        </div>
        <nav className="nav">
          <a href="#/tasks" className={route.page === "tasks" || route.page === "run" ? "is-active" : ""}>
            任务
          </a>
          <a href="#/agents" className={route.page === "agents" ? "is-active" : ""}>
            智能体
          </a>
          <a href="#/profiles" className={route.page === "profiles" ? "is-active" : ""}>
            环境
          </a>
          <a href="#/evals" className={route.page === "evals" ? "is-active" : ""}>
            评估
          </a>
        </nav>
      </aside>
      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Agent Harness Control Plane</p>
            <h2>{title}</h2>
          </div>
          <div className="topbar__meta">
            <span className="pill">API /api/v1</span>
            <span className="pill">Docker Sandbox</span>
            <span className="pill">LangGraph-ready</span>
          </div>
        </header>

        {route.page === "tasks" && <TaskInboxPage />}
        {route.page === "run" && <RunDetailPage taskId={route.taskId} runId={route.runId} />}
        {route.page === "profiles" && <ProfilesPage />}
        {route.page === "agents" && <AgentCatalogPage />}
        {route.page === "evals" && <EvalsPage />}
      </main>
    </div>
  );
}
