import { buildTaskActionBuckets } from "../../lib/presenters";
import { PanelFrame } from "../PanelFrame";

type TaskSummary = {
  id: string;
  status: string;
  created_at?: string;
};

type Props = {
  tasks: TaskSummary[];
  selectedTaskId: string;
  onSelectTask: (taskId: string) => boolean;
  onAfterSelect?: () => void;
};

export function TaskActionInbox({ tasks, selectedTaskId, onSelectTask, onAfterSelect }: Props) {
  const buckets = buildTaskActionBuckets(tasks);

  return (
    <PanelFrame title="待处理收件箱" description="优先处理阻塞任务，再继续推进执行。">
      <div className="task-inbox">
        {buckets.map((bucket) => {
          const isActive = bucket.firstTaskId && bucket.firstTaskId === selectedTaskId;
          return (
            <article key={bucket.key} className={isActive ? "task-inbox-card is-active" : "task-inbox-card"}>
              <div className="task-inbox-card__head">
                <strong>{bucket.label}</strong>
                <span className="task-inbox-card__count">{bucket.count}</span>
              </div>
              <p>{bucket.description}</p>
              <div className="inline-actions">
                <button
                  className="btn btn--secondary"
                  disabled={!bucket.firstTaskId}
                  type="button"
                  onClick={() => {
                    if (!bucket.firstTaskId) {
                      return;
                    }
                    const selected = onSelectTask(bucket.firstTaskId);
                    if (selected) {
                      onAfterSelect?.();
                    }
                  }}
                >
                  {bucket.firstTaskId ? "去处理" : "暂无任务"}
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </PanelFrame>
  );
}
