import { FormEvent, useState } from "react";

type Props = {
  onSubmit: (payload: {
    title: string;
    goal: string;
    constraints: string[];
    deliverables: string[];
    approval_mode: string;
  }) => Promise<void>;
};

export function TaskComposer({ onSubmit }: Props) {
  const [title, setTitle] = useState("");
  const [goal, setGoal] = useState("");
  const [constraints, setConstraints] = useState("不要访问未授权域名\n必须输出验证报告");
  const [deliverables, setDeliverables] = useState("脚本文件\n验证报告\n执行日志");
  const [approvalMode, setApprovalMode] = useState("high_risk");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit({
        title,
        goal,
        constraints: constraints.split("\n").map((line) => line.trim()).filter(Boolean),
        deliverables: deliverables.split("\n").map((line) => line.trim()).filter(Boolean),
        approval_mode: approvalMode,
      });
      setTitle("");
      setGoal("");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="card composer" onSubmit={handleSubmit}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">New Mission</p>
          <h3>创建新的自动化任务</h3>
        </div>
      </div>
      <label>
        <span>标题</span>
        <input value={title} onChange={(event) => setTitle(event.target.value)} required />
      </label>
      <label>
        <span>目标</span>
        <textarea value={goal} onChange={(event) => setGoal(event.target.value)} required />
      </label>
      <div className="grid two">
        <label>
          <span>约束</span>
          <textarea value={constraints} onChange={(event) => setConstraints(event.target.value)} />
        </label>
        <label>
          <span>交付物</span>
          <textarea value={deliverables} onChange={(event) => setDeliverables(event.target.value)} />
        </label>
      </div>
      <label>
        <span>审批模式</span>
        <select value={approvalMode} onChange={(event) => setApprovalMode(event.target.value)}>
          <option value="high_risk">high_risk</option>
          <option value="step">step</option>
          <option value="auto">auto</option>
        </select>
      </label>
      <button className="button button--primary" type="submit" disabled={submitting}>
        {submitting ? "提交中..." : "创建任务"}
      </button>
    </form>
  );
}
