import { useState, useEffect } from "react";
import { useToast } from "./lib/toast";
import { Layout } from "./components/Layout";
import { TaskList } from "./components/TaskList";
import { TaskDetail } from "./components/TaskDetail";
import { TaskCreate } from "./components/TaskCreate";
import { ProfilesPage } from "./components/ProfilesPage";
import { ToastViewport } from "./components/ToastViewport";

type View =
  | { type: "tasks" }
  | { type: "task-detail"; taskId: string }
  | { type: "profiles" };

export function App() {
  const [view, setView] = useState<View>(getInitialView);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const { pushToast, dismissToast, toasts } = useToast();

  useEffect(() => {
    const handler = () => {
      const hash = window.location.hash.replace("#", "") || "/tasks";
      const parts = hash.split("/").filter(Boolean);
      if (parts[0] === "tasks" && parts[1]) {
        setView({ type: "task-detail", taskId: parts[1] });
      } else if (parts[0] === "profiles") {
        setView({ type: "profiles" });
      } else {
        setView({ type: "tasks" });
      }
    };
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);

  const handleCreated = (taskId: string) => {
    window.location.hash = `#/tasks/${taskId}`;
    setView({ type: "task-detail", taskId });
  };

  return (
    <Layout>
      {view.type === "tasks" && (
        <div>
          <div className="page-header" style={{ marginBottom: "var(--space-6)" }}>
            <div className="page-header__copy">
              <h2>任务</h2>
              <p>创建和管理 AI 任务</p>
            </div>
            <div className="page-header__actions">
              <button className="btn btn--primary" onClick={() => setShowCreateModal(true)}>
                + 新建任务
              </button>
            </div>
          </div>
          <TaskList
            onSelectTask={(id) => {
              window.location.hash = `#/tasks/${id}`;
              setView({ type: "task-detail", taskId: id });
            }}
          />
        </div>
      )}

      {view.type === "task-detail" && (
        <TaskDetail
          taskId={view.taskId}
          onBack={() => {
            window.location.hash = "#/tasks";
            setView({ type: "tasks" });
          }}
        />
      )}

      {view.type === "profiles" && <ProfilesPage />}

      {showCreateModal && (
        <TaskCreate
          onClose={() => setShowCreateModal(false)}
          onCreated={handleCreated}
        />
      )}

      <ToastViewport toasts={toasts} onDismiss={dismissToast} />
    </Layout>
  );
}

function getInitialView(): View {
  const hash = window.location.hash.replace("#", "") || "/tasks";
  const parts = hash.split("/").filter(Boolean);
  if (parts[0] === "tasks" && parts[1]) {
    return { type: "task-detail", taskId: parts[1] };
  }
  if (parts[0] === "profiles") {
    return { type: "profiles" };
  }
  return { type: "tasks" };
}
