import { getPhaseLabel, getProviderLabel, getTaskStatusMeta } from "../../lib/presenters";
import { KeyValueGrid } from "../KeyValueGrid";
import { PanelFrame } from "../PanelFrame";
import { StatusBadge } from "../StatusBadge";

type RunOption = {
  id: string;
  title: string;
};

type RunSummaryData = {
  id: string;
  title: string;
  run?: { id: string; status: string; current_phase: string } | null;
  env_profile?: { name: string; provider_type: string; default_model: string } | null;
};

type Props = {
  item: RunSummaryData;
  runOptions: RunOption[];
  activeRunId: string;
  isResuming: boolean;
  onSelectRun: (runId: string) => void;
  onSubscribe: () => void;
  onResume: () => void;
};

export function RunSummary({ item, runOptions, activeRunId, isResuming, onSelectRun, onSubscribe, onResume }: Props) {
  const runStatus = getTaskStatusMeta(item.run?.status || "");

  return (
    <PanelFrame
      title="运行摘要"
      description="当前监控目标的状态、阶段与环境信息会集中显示在这里。"
      tone="accent"
      actions={<StatusBadge label={runStatus.label} tone={runStatus.tone} />}
    >
      <div className="stack run-summary-panel">
        <div className="summary-banner">
          <strong>{item.title || "未命名任务"}</strong>
          <span>{item.env_profile?.name || "未绑定环境"}</span>
        </div>
        <div className="run-summary-selector">
          <label htmlFor="run-selector">监控目标</label>
          <select
            id="run-selector"
            className="select"
            value={activeRunId}
            onChange={(event) => onSelectRun(event.target.value)}
          >
            {runOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.title}
              </option>
            ))}
          </select>
        </div>

        <KeyValueGrid
          items={[
            { label: "运行编号", value: item.run?.id || "暂无运行编号" },
            { label: "当前阶段", value: getPhaseLabel(item.run?.current_phase || "") },
            { label: "任务名称", value: item.title || "未命名任务" },
            { label: "运行环境", value: item.env_profile?.name || "未绑定环境" },
            { label: "Provider", value: getProviderLabel(item.env_profile?.provider_type || "") },
            { label: "默认模型", value: item.env_profile?.default_model || "未设置" }
          ]}
        />

        <div className="inline-actions">
          <button className="btn btn--primary" type="button" onClick={onSubscribe}>
            订阅事件
          </button>
          <button className="btn btn--secondary" disabled={isResuming} type="button" onClick={onResume}>
            {isResuming ? "恢复中..." : "恢复执行"}
          </button>
        </div>
      </div>
    </PanelFrame>
  );
}
