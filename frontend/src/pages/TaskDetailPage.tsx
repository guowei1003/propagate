import { FormEvent, useMemo, useState } from "react";

import { postJson } from "../lib/api";

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
  env_profile?: { name: string } | null;
  requirement?: Record<string, unknown> | null;
  clarification_rounds?: ClarificationRound[];
  subtasks?: Array<{ id: string; name: string; status: string }>;
};

type Props = {
  task: TaskDetail;
  onRefresh: () => Promise<void>;
};

export function TaskDetailPage({ task, onRefresh }: Props) {
  const pendingRound = useMemo(
    () => (task.clarification_rounds || []).find((item) => item.status === "pending"),
    [task.clarification_rounds]
  );
  const [answers, setAnswers] = useState<Record<string, string>>({});

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!pendingRound) return;
    await postJson(`/v2/tasks/${task.id}/clarifications/${pendingRound.id}/answer`, { answers });
    setAnswers({});
    await onRefresh();
  }

  return (
    <article className="panel">
      <h2>任务详情</h2>
      <div className="stack">
        <div className="card">
          <strong>{task.title}</strong>
          <span>Status: {task.status}</span>
          <span>Phase: {task.current_phase}</span>
          <span>Profile: {task.env_profile?.name || "-"}</span>
          {task.status === "WAITING_USER_INPUT" && <span>下一步：补充澄清信息</span>}
          {task.status === "RUNNING" && <span>下一步：前往运行监控查看审批和执行进度</span>}
        </div>
        <pre>{JSON.stringify(task.requirement || {}, null, 2)}</pre>
        <pre>{JSON.stringify(task.subtasks || [], null, 2)}</pre>
        {pendingRound && (
          <form className="form" onSubmit={(event) => void handleSubmit(event)}>
            <h3>澄清问答</h3>
            {(pendingRound.questions || []).map((question) => (
              <label key={question.key}>
                {question.question}
                <input
                  value={answers[question.key] || ""}
                  onChange={(event) => setAnswers({ ...answers, [question.key]: event.target.value })}
                />
              </label>
            ))}
            <button type="submit">提交澄清</button>
          </form>
        )}
      </div>
    </article>
  );
}
