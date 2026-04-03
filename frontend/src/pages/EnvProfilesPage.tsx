import { FormEvent, useEffect, useState } from "react";

import { MetricStrip } from "../components/MetricStrip";
import { PageHeader } from "../components/PageHeader";
import { ProfileCatalog } from "../components/profiles/ProfileCatalog";
import { ProfileFormPanel } from "../components/profiles/ProfileFormPanel";
import { StatusBadge } from "../components/StatusBadge";
import { getErrorMessage, getJson, postJson, putJson } from "../lib/api";
import { buildProfileMetrics } from "../lib/presenters";

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

const initialForm = {
  name: "",
  provider_type: "demo",
  api_base_url: "",
  api_key: "",
  default_model: "demo-heuristic",
  review_model: "",
  test_model: "",
  capability_generation_model: "",
  report_model: "",
  temperature: 0.2,
  default_timeout_sec: 300,
  max_retries: 2,
  max_concurrency: 2,
  enable_docker_sandbox: true,
  enable_auto_sub_agents: true
};

type Props = {
  meta: {
    eyebrow: string;
    title: string;
    description: string;
  };
  onStatsChange: (update: { taskCount?: number; profileCount?: number; pendingCapabilities?: number }) => void;
};

export function EnvProfilesPage({ meta, onStatsChange }: Props) {
  const [items, setItems] = useState<EnvProfile[]>([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState("");
  const [validationMessageById, setValidationMessageById] = useState<Record<string, string>>({});
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pendingValidationId, setPendingValidationId] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function refresh() {
    setIsRefreshing(true);
    setErrorMessage("");

    try {
      const profileItems = await getJson<EnvProfile[]>("/v2/env-profiles");
      setItems(profileItems);
      onStatsChange({ profileCount: profileItems.length });
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsRefreshing(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleSubmit(event?: FormEvent) {
    event?.preventDefault();
    setIsSubmitting(true);
    setErrorMessage("");

    try {
      if (editingId) {
        await putJson(`/v2/env-profiles/${editingId}`, form);
      } else {
        await postJson("/v2/env-profiles", form);
      }
      setForm(initialForm);
      setEditingId("");
      await refresh();
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleValidate(id: string) {
    setPendingValidationId(id);
    setErrorMessage("");
    try {
      const result = await postJson<{ message: string }>(`/v2/env-profiles/${id}/validate`, {});
      setValidationMessageById((current) => ({ ...current, [id]: result.message }));
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setPendingValidationId("");
    }
  }

  async function handleEdit(id: string) {
    setErrorMessage("");
    try {
      const detail = await getJson<EnvProfile>(`/v2/env-profiles/${id}`);
      setEditingId(id);
      setForm({
        name: detail.name,
        provider_type: detail.provider_type,
        api_base_url: detail.api_base_url,
        api_key: "",
        default_model: detail.default_model,
        review_model: detail.review_model,
        test_model: detail.test_model,
        capability_generation_model: detail.capability_generation_model,
        report_model: detail.report_model,
        temperature: detail.temperature,
        default_timeout_sec: detail.default_timeout_sec,
        max_retries: detail.max_retries,
        max_concurrency: detail.max_concurrency,
        enable_docker_sandbox: detail.enable_docker_sandbox,
        enable_auto_sub_agents: detail.enable_auto_sub_agents
      });
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    }
  }

  function handleFormChange<K extends keyof typeof initialForm>(key: K, value: (typeof initialForm)[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  return (
    <section className="page-section profiles-layout">
      <PageHeader
        eyebrow={meta.eyebrow}
        title={meta.title}
        description={meta.description}
        actions={
          <StatusBadge
            label={editingId ? "正在编辑" : "新增环境配置"}
            tone={editingId ? "warning" : "info"}
          />
        }
      />
      {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}
      <MetricStrip items={buildProfileMetrics(items, editingId)} />
      <div className="profiles-console-grid">
        <div className="profiles-console-grid__form">
          <form onSubmit={(event) => void handleSubmit(event)}>
            <ProfileFormPanel
              form={form}
              editingId={editingId}
              isSubmitting={isSubmitting}
              onChange={handleFormChange}
              onSubmit={() => void handleSubmit()}
            />
          </form>
        </div>
        <div className="profiles-console-grid__catalog">
          <ProfileCatalog
            items={items}
            validationMessageById={validationMessageById}
            pendingValidationId={pendingValidationId}
            onEdit={(id) => void handleEdit(id)}
            onValidate={(id) => void handleValidate(id)}
          />
        </div>
      </div>
    </section>
  );
}
