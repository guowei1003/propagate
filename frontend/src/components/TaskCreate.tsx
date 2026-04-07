import { useState, useCallback, useRef } from "react";
import { postJson } from "../lib/api";
import { useToast } from "../lib/toast";

type Props = {
  onClose: () => void;
  onCreated: (taskId: string) => void;
};

export function TaskCreate({ onClose, onCreated }: Props) {
  const { pushToast } = useToast();
  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);

  const handleSubmit = useCallback(async () => {
    if (!title.trim() || !prompt.trim()) {
      pushToast({ message: "请填写标题和任务描述", tone: "warning" });
      return;
    }
    setSubmitting(true);
    try {
      const task = await postJson<{ id: string }>("/api/tasks", {
        title: title.trim(),
        prompt: prompt.trim()
      });
      pushToast({ message: "任务已创建", tone: "success" });
      onCreated(task.id);
      onClose();
    } catch (e) {
      pushToast({ message: `创建失败: ${e instanceof Error ? e.message : String(e)}`, tone: "error" });
    } finally {
      setSubmitting(false);
    }
  }, [title, prompt, pushToast, onCreated, onClose]);

  return (
    <div
      className="modal-overlay"
      ref={overlayRef}
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
    >
      <div className="modal-panel">
        <div className="modal-header">
          <div>
            <h2>新建任务</h2>
            <p>描述你想要完成的任务，AI 将自动规划并执行</p>
          </div>
          <button className="btn btn--ghost" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <div className="field">
              <label htmlFor="task-title">任务标题</label>
              <input
                id="task-title"
                type="text"
                className="input"
                placeholder="简洁描述任务目标"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={255}
                autoFocus
              />
            </div>
          </div>
          <div className="form-group">
            <div className="field">
              <label htmlFor="task-prompt">任务描述</label>
              <textarea
                id="task-prompt"
                className="textarea"
                placeholder="详细描述任务内容，例如：帮我写一个 Python 脚本来分析当前目录下所有 CSV 文件..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={6}
              />
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn--ghost" onClick={onClose}>取消</button>
          <button
            className="btn btn--primary"
            onClick={handleSubmit}
            disabled={submitting || !title.trim() || !prompt.trim()}
          >
            {submitting ? "创建中..." : "创建任务"}
          </button>
        </div>
      </div>
    </div>
  );
}
