import { useEffect, useState } from "react";

import { AppSidebar } from "./components/AppSidebar";
import { ConsoleTopbar } from "./components/ConsoleTopbar";
import { ArtifactsPage } from "./pages/ArtifactsPage";
import { CapabilitiesPage } from "./pages/CapabilitiesPage";
import { EnvProfilesPage } from "./pages/EnvProfilesPage";
import { RunsPage } from "./pages/RunsPage";
import { TasksPage } from "./pages/TasksPage";
import {
  applyThemeToDocument,
  getStoredThemeMode,
  getSystemTheme,
  persistThemeMode,
  resolveTheme,
  type ResolvedTheme,
  type ThemeMode
} from "./lib/theme";

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

type TaskNavigationContext = {
  taskId?: string;
  runId?: string;
  navigationVersion: number;
};

const views: ViewMeta[] = [
  {
    key: "tasks",
    label: "任务中心",
    eyebrow: "任务中心",
    title: "任务中心",
    description: "快速新建任务、补充信息、查看执行流程并落地交付结果。"
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
  const [taskNavContext, setTaskNavContext] = useState<TaskNavigationContext>({
    taskId: "",
    runId: "",
    navigationVersion: 0
  });
  const [stats, setStats] = useState<AppStats>({
    taskCount: 0,
    profileCount: 0,
    pendingCapabilities: 0
  });
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => getStoredThemeMode());
  const [systemTheme, setSystemTheme] = useState<ResolvedTheme>(() => getSystemTheme());

  useEffect(() => {
    const hash = window.location.hash.replace("#", "") as ViewKey;
    if (hash && views.some((item) => item.key === hash)) {
      setView(hash);
    }
  }, []);

  useEffect(() => {
    window.location.hash = view;
  }, [view]);

  useEffect(() => {
    if (themeMode === "system") {
      setSystemTheme(getSystemTheme());
    }
  }, [themeMode]);

  useEffect(() => {
    if (themeMode !== "system") {
      return;
    }

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = (event: MediaQueryListEvent) => {
      setSystemTheme(event.matches ? "dark" : "light");
    };

    if (typeof media.addEventListener === "function") {
      media.addEventListener("change", handleChange);
      return () => media.removeEventListener("change", handleChange);
    }

    media.addListener(handleChange);
    return () => media.removeListener(handleChange);
  }, [themeMode]);

  useEffect(() => {
    persistThemeMode(themeMode);
  }, [themeMode]);

  const resolvedTheme = resolveTheme(themeMode, systemTheme);

  useEffect(() => {
    applyThemeToDocument(resolvedTheme);
  }, [resolvedTheme]);

  const currentView = views.find((item) => item.key === view) || views[0];

  function handleStatsChange(update: Partial<AppStats>) {
    setStats((current) => ({ ...current, ...update }));
  }

  function handleTaskNavigate(
    nextView: ViewKey,
    context?: {
      taskId?: string;
      runId?: string;
    }
  ) {
    if (nextView === "runs" || nextView === "artifacts") {
      setTaskNavContext((current) => ({
        taskId: context?.taskId || "",
        runId: context?.runId || "",
        navigationVersion: current.navigationVersion + 1
      }));
    }
    setView(nextView);
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
      <div className="workspace-shell">
        <ConsoleTopbar
          eyebrow={currentView.eyebrow}
          title={currentView.title}
          description={currentView.description}
          themeMode={themeMode}
          resolvedTheme={resolvedTheme}
          onThemeModeChange={setThemeMode}
        />
        <main className="workspace">
          <div key={view} className="workspace-transition">
            {view === "tasks" && (
              <TasksPage meta={currentView} onNavigate={handleTaskNavigate} onStatsChange={handleStatsChange} />
            )}
            {view === "runs" && (
              <RunsPage meta={currentView} onStatsChange={handleStatsChange} taskNavContext={taskNavContext} />
            )}
            {view === "capabilities" && <CapabilitiesPage meta={currentView} onStatsChange={handleStatsChange} />}
            {view === "profiles" && <EnvProfilesPage meta={currentView} onStatsChange={handleStatsChange} />}
            {view === "artifacts" && (
              <ArtifactsPage meta={currentView} onStatsChange={handleStatsChange} taskNavContext={taskNavContext} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
