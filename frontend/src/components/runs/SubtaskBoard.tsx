import { getSubtaskStatusMeta } from "../../lib/presenters";
import { EmptyState } from "../EmptyState";
import { PanelFrame } from "../PanelFrame";
import { StatusBadge } from "../StatusBadge";

type Subtask = {
  id: string;
  name: string;
  status: string;
  output_summary?: { selected_model?: string } | null;
};

type Props = {
  subtasks: Subtask[];
};

export function SubtaskBoard({ subtasks }: Props) {
  return (
    <PanelFrame title="子任务状态板" description="按执行状态快速判断当前链路是推进中、待重试还是需要人工介入。">
      {subtasks.length === 0 ? (
        <EmptyState
          title="子任务状态将在拆解完成后出现"
          description="当系统进入子任务执行阶段，这里会展示每个节点的状态与模型选择。"
          aside="等待任务进入执行阶段"
        />
      ) : (
        <div className="subtask-list">
          {subtasks.map((subtask) => {
            const meta = getSubtaskStatusMeta(subtask.status);
            return (
              <article key={subtask.id} className="subtask-row">
                <div className="subtask-row__meta">
                  <strong>{subtask.name}</strong>
                  <StatusBadge label={meta.label} tone={meta.tone} />
                </div>
                <div className="task-row__meta">
                  <span>模型：{subtask.output_summary?.selected_model || "未返回"}</span>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </PanelFrame>
  );
}
