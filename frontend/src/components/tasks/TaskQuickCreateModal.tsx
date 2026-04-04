import { useEffect, useState } from "react";

import { EmptyState } from "../EmptyState";

type ModelOverrides = {
  review: string;
  test: string;
  report: string;
  capability_generation: string;
};

type EnvProfile = {
  id: string;
  name: string;
};

type Props = {
  open: boolean;
  profiles: EnvProfile[];
  prompt: string;
  envProfileId: string;
  modelOverrides: ModelOverrides;
  isSubmitting: boolean;
  errorMessage: string;
  successMessage: string;
  onPromptChange: (value: string) => void;
  onEnvProfileChange: (value: string) => void;
  onModelOverridesChange: (value: ModelOverrides) => void;
  onClose: () => void;
  onNavigateProfiles: () => void;
  onSubmit: () => void;
};

const templates = [
  {
    key: "bugfix",
    label: "缺陷修复",
    prompt: "修复线上关键缺陷，包含根因分析、修复实现、回归验证和发布说明。"
  },
  {
    key: "feature",
    label: "需求改造",
    prompt: "完成业务需求改造，给出实现方案、代码变更、测试结果和上线注意事项。"
  },
  {
    key: "doc",
    label: "文档交付",
    prompt: "整理并输出可交付文档，包含使用说明、接口约定、部署步骤与验收标准。"
  },
  {
    key: "process",
    label: "流程优化",
    prompt: "优化现有执行流程，给出瓶颈分析、优化方案、落地步骤和效果评估。"
  }
] as const;

export function TaskQuickCreateModal({
  open,
  profiles,
  prompt,
  envProfileId,
  modelOverrides,
  isSubmitting,
  errorMessage,
  successMessage,
  onPromptChange,
  onEnvProfileChange,
  onModelOverridesChange,
  onClose,
  onNavigateProfiles,
  onSubmit
}: Props) {
  const [showOverrides, setShowOverrides] = useState(false);

  useEffect(() => {
    if (!open) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  return (
    <div className="modal-overlay" onClick={onClose} role="presentation">
      <section
        aria-modal="true"
        className="modal-panel"
        role="dialog"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="modal-header">
          <div>
            <h3>新建任务</h3>
            <p>填写最少信息即可发起，系统会自动进入后续执行流程。</p>
          </div>
          <button className="btn btn--ghost" type="button" onClick={onClose}>
            关闭
          </button>
        </header>

        <div className="modal-body">
          {errorMessage ? <div className="modal-feedback modal-feedback--error">{errorMessage}</div> : null}
          {successMessage ? <div className="modal-feedback modal-feedback--success">{successMessage}</div> : null}

          {profiles.length === 0 ? (
            <EmptyState
              title="还没有可用运行环境"
              description="请先配置运行环境，再创建任务。"
              action={
                <button className="btn btn--primary" type="button" onClick={onNavigateProfiles}>
                  前往运行环境
                </button>
              }
            />
          ) : (
            <div className="form-grid">
              <section className="form-group">
                <div className="form-group__header">
                  <strong>任务模板</strong>
                  <p>可一键填入常见任务描述，再按需修改。</p>
                </div>
                <div className="task-template-list">
                  {templates.map((item) => (
                    <button
                      key={item.key}
                      className="btn btn--ghost task-template-chip"
                      type="button"
                      onClick={() => onPromptChange(item.prompt)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </section>

              <section className="form-group">
                <div className="field">
                  <span className="field__label">需求描述</span>
                  <textarea
                    className="textarea"
                    rows={7}
                    value={prompt}
                    onChange={(event) => onPromptChange(event.target.value)}
                    placeholder="请写明目标、约束和预期交付。"
                  />
                </div>
                <div className="field">
                  <span className="field__label">运行环境</span>
                  <select className="select" value={envProfileId} onChange={(event) => onEnvProfileChange(event.target.value)}>
                    {profiles.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </div>
              </section>

              <section className="form-group">
                <div className="inline-actions">
                  <button className="btn btn--ghost" type="button" onClick={() => setShowOverrides((current) => !current)}>
                    {showOverrides ? "收起高级设置" : "展开高级设置"}
                  </button>
                </div>
                {showOverrides ? (
                  <div className="field-list">
                    <div className="field">
                      <span className="field__label">Review 模型覆盖</span>
                      <input
                        className="input"
                        value={modelOverrides.review}
                        onChange={(event) => onModelOverridesChange({ ...modelOverrides, review: event.target.value })}
                      />
                    </div>
                    <div className="field">
                      <span className="field__label">Test 模型覆盖</span>
                      <input
                        className="input"
                        value={modelOverrides.test}
                        onChange={(event) => onModelOverridesChange({ ...modelOverrides, test: event.target.value })}
                      />
                    </div>
                    <div className="field">
                      <span className="field__label">Report 模型覆盖</span>
                      <input
                        className="input"
                        value={modelOverrides.report}
                        onChange={(event) => onModelOverridesChange({ ...modelOverrides, report: event.target.value })}
                      />
                    </div>
                    <div className="field">
                      <span className="field__label">Capability 模型覆盖</span>
                      <input
                        className="input"
                        value={modelOverrides.capability_generation}
                        onChange={(event) =>
                          onModelOverridesChange({ ...modelOverrides, capability_generation: event.target.value })
                        }
                      />
                    </div>
                  </div>
                ) : null}
              </section>
            </div>
          )}
        </div>

        <footer className="modal-footer">
          <button className="btn btn--ghost" type="button" onClick={onClose}>
            取消
          </button>
          <button
            className="btn btn--primary"
            disabled={isSubmitting || profiles.length === 0 || !prompt.trim() || !envProfileId}
            type="button"
            onClick={onSubmit}
          >
            {isSubmitting ? "创建中..." : "创建任务"}
          </button>
        </footer>
      </section>
    </div>
  );
}
