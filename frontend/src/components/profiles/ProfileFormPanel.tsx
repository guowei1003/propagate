import { formatBooleanLabel, getProviderLabel } from "../../lib/presenters";
import { PanelFrame } from "../PanelFrame";

type FormState = {
  name: string;
  provider_type: string;
  api_base_url: string;
  api_key: string;
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
};

type Props = {
  form: FormState;
  editingId: string;
  isSubmitting: boolean;
  onChange: (key: keyof FormState, value: FormState[keyof FormState]) => void;
  onSubmit: () => void;
};

export function ProfileFormPanel({ form, editingId, isSubmitting, onChange, onSubmit }: Props) {
  return (
    <PanelFrame
      title={editingId ? "正在编辑环境配置" : "新增环境配置"}
      description="把基础接入、模型策略、执行限制和开关统一收束在一个运行配置台里。"
      tone="accent"
    >
      <div className="form-grid">
        <section className="form-group">
          <div className="form-group__header">
            <strong>基础接入</strong>
            <p>先定义环境名称、Provider 和 API 接入参数。</p>
          </div>
          <div className="field-list">
            <div className="field">
              <span className="field__label">环境名称</span>
              <input className="input" value={form.name} onChange={(event) => onChange("name", event.target.value)} />
            </div>
            <div className="field-inline">
              <div className="field">
                <span className="field__label">Provider</span>
                <select
                  className="select"
                  value={form.provider_type}
                  onChange={(event) => onChange("provider_type", event.target.value)}
                >
                  <option value="demo">{getProviderLabel("demo")}</option>
                  <option value="openai_compatible">{getProviderLabel("openai_compatible")}</option>
                </select>
              </div>
              <div className="field">
                <span className="field__label">默认模型</span>
                <input
                  className="input"
                  value={form.default_model}
                  onChange={(event) => onChange("default_model", event.target.value)}
                />
              </div>
            </div>
            <div className="field">
              <span className="field__label">API Base URL</span>
              <input
                className="input"
                value={form.api_base_url}
                onChange={(event) => onChange("api_base_url", event.target.value)}
              />
            </div>
            <div className="field">
              <span className="field__label">API Key</span>
              <input
                className="input"
                type="password"
                value={form.api_key}
                onChange={(event) => onChange("api_key", event.target.value)}
              />
            </div>
          </div>
        </section>

        <section className="form-group">
          <div className="form-group__header">
            <strong>模型配置</strong>
            <p>需要分阶段细化模型时，可以分别覆盖 review、test、capability 与 report。</p>
          </div>
          <div className="field-list">
            <div className="field">
              <span className="field__label">Review 模型</span>
              <input
                className="input"
                value={form.review_model}
                onChange={(event) => onChange("review_model", event.target.value)}
              />
            </div>
            <div className="field">
              <span className="field__label">Test 模型</span>
              <input
                className="input"
                value={form.test_model}
                onChange={(event) => onChange("test_model", event.target.value)}
              />
            </div>
            <div className="field">
              <span className="field__label">Capability 生成模型</span>
              <input
                className="input"
                value={form.capability_generation_model}
                onChange={(event) => onChange("capability_generation_model", event.target.value)}
              />
            </div>
            <div className="field">
              <span className="field__label">Report 模型</span>
              <input
                className="input"
                value={form.report_model}
                onChange={(event) => onChange("report_model", event.target.value)}
              />
            </div>
          </div>
        </section>

        <section className="form-group">
          <div className="form-group__header">
            <strong>执行限制</strong>
            <p>统一控制温度、默认超时、重试上限和并发策略。</p>
          </div>
          <div className="field-inline">
            <div className="field">
              <span className="field__label">Temperature</span>
              <input
                className="input"
                type="number"
                step="0.1"
                value={form.temperature}
                onChange={(event) => onChange("temperature", Number(event.target.value))}
              />
            </div>
            <div className="field">
              <span className="field__label">默认超时（秒）</span>
              <input
                className="input"
                type="number"
                value={form.default_timeout_sec}
                onChange={(event) => onChange("default_timeout_sec", Number(event.target.value))}
              />
            </div>
          </div>
          <div className="field-inline">
            <div className="field">
              <span className="field__label">最大重试次数</span>
              <input
                className="input"
                type="number"
                value={form.max_retries}
                onChange={(event) => onChange("max_retries", Number(event.target.value))}
              />
            </div>
            <div className="field">
              <span className="field__label">最大并发数</span>
              <input
                className="input"
                type="number"
                value={form.max_concurrency}
                onChange={(event) => onChange("max_concurrency", Number(event.target.value))}
              />
            </div>
          </div>
        </section>

        <section className="form-group">
          <div className="form-group__header">
            <strong>执行开关</strong>
            <p>直接控制是否允许 Docker 沙箱与自动子代理能力参与执行。</p>
          </div>
          <div className="field-list">
            <label className="checkbox-field">
              <input
                checked={form.enable_docker_sandbox}
                type="checkbox"
                onChange={(event) => onChange("enable_docker_sandbox", event.target.checked)}
              />
              Docker Sandbox：{formatBooleanLabel(form.enable_docker_sandbox)}
            </label>
            <label className="checkbox-field">
              <input
                checked={form.enable_auto_sub_agents}
                type="checkbox"
                onChange={(event) => onChange("enable_auto_sub_agents", event.target.checked)}
              />
              Auto Sub Agents：{formatBooleanLabel(form.enable_auto_sub_agents)}
            </label>
          </div>
        </section>

        <div className="profile-form-actions">
          <button className="btn btn--primary" disabled={isSubmitting} type="button" onClick={onSubmit}>
            {isSubmitting ? "保存中..." : "保存配置"}
          </button>
        </div>
      </div>
    </PanelFrame>
  );
}
