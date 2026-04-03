import { useEffect, useState } from "react";

import { AppSidebar } from "./components/AppSidebar";
import { ArtifactsPage } from "./pages/ArtifactsPage";
import { CapabilitiesPage } from "./pages/CapabilitiesPage";
import { EnvProfilesPage } from "./pages/EnvProfilesPage";
import { RunsPage } from "./pages/RunsPage";
import { TasksPage } from "./pages/TasksPage";

type ViewKey = "tasks" | "runs" | "capabilities" | "profiles" | "artifacts";

type ViewMeta = {
  key: ViewKey;
  label: string;
  eyebrow: string;
  title: string;
  description: string;
};

type AppStats = {
  taskCount: number;
  profileCount: number;
  pendingCapabilities: number;
};

const views: ViewMeta[] = [
  {
    key: "tasks",
    label: "任务编排",
    eyebrow: "Task Orchestration",
    title: "任务编排",
    description: "从需求输入、环境选择到澄清补充，所有新任务在这里进入执行链路。"
  },
  {
    key: "runs",
    label: "执行流监控",
    eyebrow: "Run Monitoring",
    title: "执行流监控",
    description: "查看运行阶段、依赖阻塞、事件流和人工介入入口。"
  },
  {
    key: "capabilities",
    label: "能力审批",
    eyebrow: "Capability Review",
    title: "能力审批",
    description: "对高风险能力进行快速判断，确保运行链路只在可控条件下推进。"
  },
  {
    key: "profiles",
    label: "运行环境",
    eyebrow: "Runtime Profiles",
    title: "运行环境",
    description: "管理模型接入、并发策略、超时与执行限制。"
  },
  {
    key: "artifacts",
    label: "交付产物",
    eyebrow: "Delivery Artifacts",
    title: "交付产物",
    description: "查看本次运行的产物状态、Bundle 输出和交付入口。"
  }
];

export default function App() {
  const [view, setView] = useState<ViewKey>("tasks");
  const [stats, setStats] = useState<AppStats>({
    taskCount: 0,
    profileCount: 0,
    pendingCapabilities: 0
  });

  useEffect(() => {
    const hash = window.location.hash.replace("#", "") as ViewKey;
    if (hash && views.some((item) => item.key === hash)) {
      setView(hash);
    }
  }, []);

  useEffect(() => {
    window.location.hash = view;
  }, [view]);

  const currentView = views.find((item) => item.key === view) || views[0];

  function handleStatsChange(update: Partial<AppStats>) {
    setStats((current) => ({ ...current, ...update }));
  }

  return (
    <div className="app-shell">
      <AppSidebar
        currentViewLabel={currentView.label}
        pendingCapabilitiesLabel={String(stats.pendingCapabilities)}
        stats={stats}
        view={view}
        views={views}
        onChange={(nextView) => setView(nextView as ViewKey)}
      />
      <main className="workspace">
        <div key={view} className="workspace-transition">
          {view === "tasks" && <TasksPage meta={currentView} onNavigate={setView} onStatsChange={handleStatsChange} />}
          {view === "runs" && <RunsPage meta={currentView} onStatsChange={handleStatsChange} />}
          {view === "capabilities" && <CapabilitiesPage meta={currentView} onStatsChange={handleStatsChange} />}
          {view === "profiles" && <EnvProfilesPage meta={currentView} onStatsChange={handleStatsChange} />}
          {view === "artifacts" && <ArtifactsPage meta={currentView} onStatsChange={handleStatsChange} />}
        </div>
      </main>
    </div>
  );
}
