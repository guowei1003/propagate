import { EmptyState } from "../EmptyState";
import { KeyValueGrid } from "../KeyValueGrid";
import { PanelFrame } from "../PanelFrame";
import { RawJsonBlock } from "../RawJsonBlock";

type Props = {
  runId: string;
  taskTitle: string;
  artifacts: Record<string, unknown> | null;
  isBuilding: boolean;
  onBuild: () => void;
};

function toArtifactSummary(artifacts: Record<string, unknown> | null) {
  if (!artifacts) {
    return [];
  }

  return Object.entries(artifacts).slice(0, 6).map(([key, value]) => ({
    label: key,
    value: typeof value === "object" ? JSON.stringify(value) : String(value)
  }));
}

export function ArtifactBundlePanel({ runId, taskTitle, artifacts, isBuilding, onBuild }: Props) {
  if (!runId) {
    return (
      <PanelFrame title="交付概览" description="运行完成后，这里会显示可交付产物和 Bundle 入口。">
        <EmptyState
          title="完成一次运行后，这里会生成交付产物"
          description="当前还没有找到可用于交付的运行，请先推进任务进入执行并完成产出。"
          aside="等待可交付运行"
        />
      </PanelFrame>
    );
  }

  return (
    <PanelFrame
      title="交付概览"
      description="这里会聚焦最近运行的产物摘要、Bundle 动作和原始交付信息。"
      tone="accent"
    >
      <div className="stack">
        <article className="artifact-summary">
          <div className="artifact-summary__header">
            <div className="artifact-summary__meta">
              <span>任务：{taskTitle || "未命名任务"}</span>
              <span>
                Run：<code>{runId}</code>
              </span>
            </div>
          </div>
          <div className="artifact-summary__actions">
            <button className="btn btn--primary" disabled={isBuilding} type="button" onClick={onBuild}>
              {isBuilding ? "构建中..." : "构建 Bundle"}
            </button>
            <a className="btn btn--ghost" href={`/v2/runs/${runId}/bundle/download`} rel="noreferrer" target="_blank">
              下载 Bundle
            </a>
          </div>
        </article>

        {toArtifactSummary(artifacts).length > 0 ? (
          <KeyValueGrid items={toArtifactSummary(artifacts)} columns={2} />
        ) : (
          <div className="inspector-note">当前还没有产物摘要，可以先构建 Bundle 或等待任务生成更多交付信息。</div>
        )}

        <RawJsonBlock title="查看原始产物信息" data={artifacts || {}} />
      </div>
    </PanelFrame>
  );
}
