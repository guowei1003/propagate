import { getPhaseLabel, getTaskStatusMeta } from "../../lib/presenters";
import { PanelFrame } from "../PanelFrame";
import { StatusBadge } from "../StatusBadge";
import { EmptyState } from "../EmptyState";

type TaskSummary = {
  id: string;
  title: string;
  status: string;
  current_phase: string;
  env_profile?: { name: string } | null;
  run?: { id: string } | null;
  subtasks?: Array<{ id: string; name: string; status: string }>;
};

type Props = {
  tasks: TaskSummary[];
  selectedTaskId: string;
  isRefreshing: boolean;
  onSelect: (taskId: string) => void;
  onNavigateRuns: () => void;
};

export function TaskQueue({ tasks, selectedTaskId, isRefreshing, onSelect, onNavigateRuns }: Props) {
  return (
    <PanelFrame
      title="任务队列"
      description="优先查看当前阶段、环境与子任务规模，决定是否需要进一步进入监控。"
      actions={<span className="pill-note">{isRefreshing ? "同步中" : `${tasks.length} 条任务`}</span>}
    >
      {tasks.length === 0 ? (
        <EmptyState
          title="还没有任务进入执行链路"
          description="创建一个新任务后，这里会显示状态、阶段与下一步动作。"
          aside="从左侧创建器开始"
        />
      ) : (
        <div className="task-queue">
          {tasks.map((item) => {
            const statusMeta = getTaskStatusMeta(item.status);
            return (
              <article
                key={item.id}
                className={item.id === selectedTaskId ? "task-row is-active" : "task-row"}
              >
                <div className="task-row__header">
                  <div className="task-row__title">
                    <strong>{item.title || "未命名任务"}</strong>
                    <div className="task-row__meta">
                      <span>{getPhaseLabel(item.current_phase)}</span>
                      <span>{item.env_profile?.name || "未绑定环境"}</span>
                      <span>{item.subtasks?.length || 0} 个子任务</span>
                    </div>
                  </div>
                  <StatusBadge label={statusMeta.label} tone={statusMeta.tone} />
                </div>
                <div className="task-row__actions">
                  <button className="btn btn--secondary" type="button" onClick={() => onSelect(item.id)}>
                    查看详情
                  </button>
                  <button className="btn btn--ghost" type="button" onClick={onNavigateRuns}>
                    前往监控
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </PanelFrame>
  );
}
