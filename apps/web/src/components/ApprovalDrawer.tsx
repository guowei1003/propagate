import type { Approval } from "../lib/types";

type Props = {
  approvals: Approval[];
  onApprove: (approvalId: string) => Promise<void>;
  onReject: (approvalId: string) => Promise<void>;
};

export function ApprovalDrawer({ approvals, onApprove, onReject }: Props) {
  const pending = approvals.filter((approval) => approval.status === "pending");

  return (
    <section className="card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Approvals</p>
          <h3>审批队列</h3>
        </div>
      </div>
      {pending.length === 0 ? (
        <p className="muted">当前没有待处理审批。</p>
      ) : (
        <div className="approval-list">
          {pending.map((approval) => (
            <article key={approval.id} className="approval-item">
              <div>
                <strong>{approval.step_id}</strong>
                <p>{approval.reason}</p>
              </div>
              <div className="button-row">
                <button className="button button--ghost" onClick={() => void onReject(approval.id)}>
                  拒绝
                </button>
                <button className="button button--primary" onClick={() => void onApprove(approval.id)}>
                  批准
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
