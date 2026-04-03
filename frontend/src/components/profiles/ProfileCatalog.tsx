import { getProviderLabel } from "../../lib/presenters";
import { EmptyState } from "../EmptyState";
import { PanelFrame } from "../PanelFrame";

type EnvProfile = {
  id: string;
  name: string;
  provider_type: string;
  api_base_url: string;
  default_model: string;
  review_model: string;
  test_model: string;
  capability_generation_model: string;
  report_model: string;
  temperature: number;
  default_timeout_sec: number;
  max_retries: number;
  max_concurrency: number;
  enable_docker_sandbox: boolean;
  enable_auto_sub_agents: boolean;
  api_key_masked: string;
};

type Props = {
  items: EnvProfile[];
  validationMessageById: Record<string, string>;
  pendingValidationId: string;
  onEdit: (id: string) => void;
  onValidate: (id: string) => void;
};

export function ProfileCatalog({
  items,
  validationMessageById,
  pendingValidationId,
  onEdit,
  onValidate
}: Props) {
  return (
    <PanelFrame title="环境目录" description="快速浏览已有环境的模型摘要、执行限制与校验结果。">
      {items.length === 0 ? (
        <EmptyState
          title="还没有可用运行环境"
          description="创建第一个运行环境后，这里会展示模型接入与执行限制摘要。"
          aside="先配置再调度"
        />
      ) : (
        <div className="profile-list">
          {items.map((item) => (
            <article key={item.id} className="profile-card">
              <div className="profile-card__header">
                <div className="profile-card__title">
                  <strong>{item.name}</strong>
                  <div className="meta-chip-list profile-card__meta">
                    <span className="meta-chip">{getProviderLabel(item.provider_type)}</span>
                    <span className="meta-chip">default: {item.default_model}</span>
                    <span className="meta-chip">review: {item.review_model || "-"}</span>
                    <span className="meta-chip">test: {item.test_model || "-"}</span>
                    <span className="meta-chip">capability: {item.capability_generation_model || "-"}</span>
                    <span className="meta-chip">report: {item.report_model || "-"}</span>
                    <span className="meta-chip">timeout: {item.default_timeout_sec}</span>
                    <span className="meta-chip">retries: {item.max_retries}</span>
                    <span className="meta-chip">concurrency: {item.max_concurrency}</span>
                    <span className="meta-chip">key: {item.api_key_masked || "-"}</span>
                  </div>
                </div>
              </div>

              <div className="inline-actions">
                <button className="btn btn--secondary" type="button" onClick={() => onEdit(item.id)}>
                  编辑
                </button>
                <button
                  className="btn btn--ghost"
                  disabled={pendingValidationId === item.id}
                  type="button"
                  onClick={() => onValidate(item.id)}
                >
                  {pendingValidationId === item.id ? "校验中..." : "校验"}
                </button>
              </div>

              {validationMessageById[item.id] ? (
                <div className="profile-validation-note">{validationMessageById[item.id]}</div>
              ) : null}
            </article>
          ))}
        </div>
      )}
    </PanelFrame>
  );
}
