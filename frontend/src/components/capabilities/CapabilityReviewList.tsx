import { getRiskLevelMeta } from "../../lib/presenters";
import { EmptyState } from "../EmptyState";
import { PanelFrame } from "../PanelFrame";
import { StatusBadge } from "../StatusBadge";

type Capability = {
  id: string;
  name: string;
  type: string;
  status: string;
  risk_score: number;
};

type Props = {
  items: Capability[];
  pendingDecisionId: string;
  onDecision: (id: string, action: "approve" | "reject") => void;
};

export function CapabilityReviewList({ items, pendingDecisionId, onDecision }: Props) {
  return (
    <PanelFrame
      title="能力审批台"
      description="优先关注高风险能力，明确当前状态后再决定是否允许其进入执行链路。"
    >
      {items.length === 0 ? (
        <EmptyState
          title="当前没有待处理能力审批"
          description="一旦出现新的能力审批记录，这里会按风险等级和当前状态集中展示。"
          aside="当前审批队列为空"
        />
      ) : (
        <div className="capability-list">
          {items.map((item) => {
            const riskMeta = getRiskLevelMeta(item.risk_score);
            return (
              <article key={item.id} className="capability-card">
                <div className="capability-card__header">
                  <div className="capability-card__title">
                    <strong>{item.name}</strong>
                    <div className="meta-chip-list task-row__meta">
                      <span className="meta-chip">类型：{item.type}</span>
                      <span className="meta-chip">状态：{item.status}</span>
                      <span className="meta-chip">风险值：{item.risk_score}</span>
                    </div>
                  </div>
                  <StatusBadge label={riskMeta.label} tone={riskMeta.tone} />
                </div>
                <div className="capability-card__actions">
                  <button
                    className="btn btn--primary"
                    disabled={pendingDecisionId === item.id}
                    type="button"
                    onClick={() => onDecision(item.id, "approve")}
                  >
                    {pendingDecisionId === item.id ? "处理中..." : "审批通过"}
                  </button>
                  <button
                    className="btn btn--danger"
                    disabled={pendingDecisionId === item.id}
                    type="button"
                    onClick={() => onDecision(item.id, "reject")}
                  >
                    驳回
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </PanelFrame>
  );
}
