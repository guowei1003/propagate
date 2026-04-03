import { useState } from "react";

import { EmptyState } from "../EmptyState";
import { PanelFrame } from "../PanelFrame";

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
  profiles: EnvProfile[];
  prompt: string;
  envProfileId: string;
  modelOverrides: ModelOverrides;
  isSubmitting: boolean;
  onPromptChange: (value: string) => void;
  onEnvProfileChange: (value: string) => void;
  onModelOverridesChange: (value: ModelOverrides) => void;
  onNavigateProfiles: () => void;
  onSubmit: () => void;
};

export function TaskComposer({
  profiles,
  prompt,
  envProfileId,
  modelOverrides,
  isSubmitting,
  onPromptChange,
  onEnvProfileChange,
  onModelOverridesChange,
  onNavigateProfiles,
  onSubmit
}: Props) {
  const [showOverrides, setShowOverrides] = useState(false);
  const selectedProfile = profiles.find((item) => item.id === envProfileId) || profiles[0] || null;
  const activeOverrideCount = Object.values(modelOverrides).filter((value) => value.trim()).length;

  if (profiles.length === 0) {
    return (
      <PanelFrame title="任务创建器" description="先选择一个可用运行环境，再让新任务进入执行链路。" tone="accent">
        <EmptyState
          title="还没有可用运行环境"
          description="先完成环境配置，任务创建器才会开放提交入口。"
          action={
            <button className="btn btn--primary" type="button" onClick={onNavigateProfiles}>
              前往运行环境
            </button>
          }
          aside="先建环境，再建任务"
        />
      </PanelFrame>
    );
  }

  return (
    <PanelFrame
      title="任务创建器"
      description="先定义需求，再决定使用哪个环境进入执行编排。"
      tone="accent"
      actions={
        <button className="btn btn--ghost" type="button" onClick={() => setShowOverrides((current) => !current)}>
          {showOverrides ? "收起模型覆盖" : "展开模型覆盖"}
        </button>
      }
    >
      <div className="form-grid task-composer">
        <div className="task-composer__summary">
          <span className="pill-note">环境：{selectedProfile?.name || "未选择"}</span>
          <span className="pill-note">
            {showOverrides ? `模型覆盖 ${activeOverrideCount} 项` : "默认使用环境模型"}
          </span>
        </div>
        <section className="form-group">
          <div className="form-group__header">
            <strong>基础任务信息</strong>
            <p>输入本次任务的需求描述，系统会自动进入需求分析与后续执行阶段。</p>
          </div>
          <div className="field">
            <span className="field__label">需求描述</span>
            <textarea
              className="textarea"
              rows={8}
              value={prompt}
              onChange={(event) => onPromptChange(event.target.value)}
              placeholder="描述你希望系统完成的目标、约束、交付形式和关键判断条件。"
            />
          </div>
        </section>

        <section className="form-group">
          <div className="form-group__header">
            <strong>环境选择</strong>
            <p>执行链路会继承这里指定的默认模型、并发和超时策略。</p>
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

        {showOverrides ? (
          <section className="form-group">
            <div className="form-group__header">
              <strong>模型覆盖</strong>
              <p>只在需要针对某个阶段强制改用模型时填写，默认情况下建议保持为空。</p>
            </div>
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
                <span className="field__label">Capability 生成模型覆盖</span>
                <input
                  className="input"
                  value={modelOverrides.capability_generation}
                  onChange={(event) =>
                    onModelOverridesChange({ ...modelOverrides, capability_generation: event.target.value })
                  }
                />
              </div>
            </div>
          </section>
        ) : null}

        <div className="inline-actions">
          <button className="btn btn--primary" disabled={isSubmitting || !prompt.trim()} type="button" onClick={onSubmit}>
            {isSubmitting ? "任务启动中..." : "启动任务编排"}
          </button>
          <span className="pill-note">创建后自动刷新队列与检视区</span>
        </div>
      </div>
    </PanelFrame>
  );
}
