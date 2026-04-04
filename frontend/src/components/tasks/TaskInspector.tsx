import { useEffect, useState } from "react";

import { getErrorMessage, postJson } from "../../lib/api";
import { getPhaseLabel, getSubtaskStatusMeta, getTaskStatusMeta } from "../../lib/presenters";
import { EmptyState } from "../EmptyState";
import { KeyValueGrid } from "../KeyValueGrid";
import { PanelFrame } from "../PanelFrame";
import { RawJsonBlock } from "../RawJsonBlock";
import { StatusBadge } from "../StatusBadge";

type ClarificationRound = {
  id: string;
  status: string;
  questions?: Array<{ key: string; question: string }>;
};

type TaskDetail = {
  id: string;
  title: string;
  status: string;
  current_phase: string;
  run?: { id: string } | null;
  env_profile?: { name: string } | null;
  requirement?: Record<string, unknown> | null;
  clarification_rounds?: ClarificationRound[];
  subtasks?: Array<{ id: string; name: string; status: string }>;
};

type Props = {
  task: TaskDetail | null;
  onNavigateRuns: (context: { taskId?: string; runId?: string }) => void;
  onNavigateArtifacts: (context: { taskId?: string; runId?: string }) => void;
  onNavigateCapabilities: () => void;
  onRefresh: () => Promise<void>;
};

function getNextActionText(task: TaskDetail): string {
  if (task.status === "WAITING_USER_INPUT") {
    return "当前任务正在等待补充信息，完成补充后会继续推进。";
  }
  if (task.status === "WAITING_APPROVAL") {
    return "当前任务正在等待能力审批，审批通过后会继续执行。";
  }
  if (task.status === "RUNNING") {
    return "当前任务正在执行，可进入执行页面查看实时推进。";
  }
  if (task.status === "FAILED") {
    return "当前任务执行失败，建议先查看执行记录定位原因。";
  }
  if (task.status === "COMPLETED" || task.status === "PARTIAL_SUCCESS") {
    return "当前任务已结束，可进入交付页查看产物与报告。";
  }
  return "系统会继续按当前阶段推进，必要时请补充信息或查看执行。";
}

export function TaskInspector({ task, onNavigateRuns, onNavigateArtifacts, onNavigateCapabilities, onRefresh }: Props) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isSubmittingAnswers, setIsSubmittingAnswers] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    setAnswers({});
    setErrorMessage("");
  }, [task?.id]);

  if (!task) {
    return (
      <PanelFrame title="任务详情" description="这里会显示当前选中任务的摘要、建议动作和原始需求。">
        <EmptyState
          title="先从队列中选择一个任务"
          description="选中任务后，这里会提供状态摘要、补充信息和子任务清单。"
          aside="任务详情保持聚焦"
        />
      </PanelFrame>
    );
  }

  const currentTask = task;
  const pendingRound = (task.clarification_rounds || []).find((item) => item.status === "pending");
  const statusMeta = getTaskStatusMeta(task.status);
  const hasRun = Boolean(task.run?.id);
  const runContext = { taskId: task.id, runId: task.run?.id || "" };

  async function handleSubmitAnswers() {
    if (!pendingRound) {
      return;
    }

    setIsSubmittingAnswers(true);
    setErrorMessage("");

    try {
      await postJson(`/v2/tasks/${currentTask.id}/clarifications/${pendingRound.id}/answer`, { answers });
      setAnswers({});
      await onRefresh();
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsSubmittingAnswers(false);
    }
  }

  return (
    <PanelFrame
      title="任务详情"
      description="在这里判断当前任务是否需要补充信息、进入审批、查看执行或检查交付。"
    >
      <div className="stack">
        {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}

        <section className="inspector-section">
          <div className="task-inspector__hero">
            <div className="task-inspector__hero-copy">
              <strong>{task.title || "未命名任务"}</strong>
              <p>{task.env_profile?.name || "未绑定环境"}</p>
            </div>
            <StatusBadge label={statusMeta.label} tone={statusMeta.tone} />
          </div>
          <KeyValueGrid
            items={[
              { label: "任务名称", value: task.title || "未命名任务" },
              { label: "当前阶段", value: getPhaseLabel(task.current_phase) },
              { label: "绑定环境", value: task.env_profile?.name || "未绑定环境" },
              { label: "子任务数量", value: String(task.subtasks?.length || 0) }
            ]}
          />
        </section>

        <section className="inspector-section">
          <strong>下一步动作</strong>
          <div className="inspector-note">{getNextActionText(task)}</div>
          <div className="inline-actions">
            {task.status === "WAITING_USER_INPUT" ? (
              <button
                className="btn btn--primary"
                disabled={!pendingRound || isSubmittingAnswers}
                type="button"
                onClick={() => void handleSubmitAnswers()}
              >
                {isSubmittingAnswers ? "提交中..." : "提交补充信息"}
              </button>
            ) : null}
            {task.status === "WAITING_APPROVAL" ? (
              <button className="btn btn--primary" type="button" onClick={onNavigateCapabilities}>
                前往能力审批
              </button>
            ) : null}
            {task.status === "RUNNING" || task.status === "FAILED" ? (
              <button
                className="btn btn--primary"
                disabled={!hasRun}
                title={hasRun ? "" : "当前任务尚未生成可查看的执行记录"}
                type="button"
                onClick={() => onNavigateRuns(runContext)}
              >
                查看执行
              </button>
            ) : null}
            {task.status === "COMPLETED" || task.status === "PARTIAL_SUCCESS" ? (
              <button
                className="btn btn--primary"
                disabled={!hasRun}
                title={hasRun ? "" : "当前任务尚未生成可查看的交付记录"}
                type="button"
                onClick={() => onNavigateArtifacts(runContext)}
              >
                查看交付产物
              </button>
            ) : null}
          </div>
        </section>

        {pendingRound ? (
          <section className="form-group inspector-section">
            <div className="form-group__header">
              <strong>补充信息</strong>
              <p>系统当前停在待补充阶段，请先回答问题，任务才会继续推进。</p>
            </div>
            <div className="field-list">
              {(pendingRound.questions || []).map((question) => (
                <div key={question.key} className="field">
                  <span className="field__label">{question.question}</span>
                  <input
                    className="input"
                    value={answers[question.key] || ""}
                    onChange={(event) => setAnswers((current) => ({ ...current, [question.key]: event.target.value }))}
                  />
                </div>
              ))}
            </div>
            <div className="inline-actions">
              <button
                className="btn btn--primary"
                disabled={isSubmittingAnswers}
                type="button"
                onClick={() => void handleSubmitAnswers()}
              >
                {isSubmittingAnswers ? "提交中..." : "提交补充信息"}
              </button>
            </div>
          </section>
        ) : null}

        <section className="inspector-section">
          <strong>子任务清单</strong>
          {(task.subtasks || []).length === 0 ? (
            <div className="inspector-note">任务还没有进入子任务执行阶段。</div>
          ) : (
            <div className="subtask-list">
              {(task.subtasks || []).map((subtask) => {
                const subtaskMeta = getSubtaskStatusMeta(subtask.status);
                return (
                  <article key={subtask.id} className="subtask-row">
                    <div className="subtask-row__meta">
                      <strong>{subtask.name}</strong>
                      <StatusBadge label={subtaskMeta.label} tone={subtaskMeta.tone} />
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        <section className="inspector-section">
          <RawJsonBlock title="查看原始需求" data={task.requirement || {}} />
        </section>
      </div>
    </PanelFrame>
  );
}
