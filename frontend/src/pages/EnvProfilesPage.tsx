import { FormEvent, useEffect, useState } from "react";

import { MetricStrip } from "../components/MetricStrip";
import { PageHeader } from "../components/PageHeader";
import { ProfileCatalog } from "../components/profiles/ProfileCatalog";
import { ProfileFormPanel } from "../components/profiles/ProfileFormPanel";
import { StatusBadge } from "../components/StatusBadge";
import { ApiError, getErrorMessage, getJson, postJson, putJson } from "../lib/api";
import { buildProfileMetrics } from "../lib/presenters";
import { type ToastAction, useToast } from "../lib/toast";

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

type ProfileValidationSnapshot = {
  status: "success" | "error";
  summary: string;
  checkedAt: string;
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

function formatCheckedAt(): string {
  return new Date().toLocaleString("zh-CN", { hour12: false });
}

export function EnvProfilesPage({ meta, onStatsChange }: Props) {
  const [items, setItems] = useState<EnvProfile[]>([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState("");
  const [validationById, setValidationById] = useState<Record<string, ProfileValidationSnapshot>>({});
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pendingValidationId, setPendingValidationId] = useState("");
  const { pushToast } = useToast();

  function notifyRequestError(
    error: unknown,
    title: string,
    options?: {
      dedupeKey?: string;
      action?: ToastAction;
    }
  ) {
    if (error instanceof ApiError && error.status === 409 && error.code === "ENV_PROFILE_NAME_CONFLICT") {
      pushToast({
        tone: "warning",
        title: "名称冲突",
        message: "环境配置名称已存在，请更换名称后重试。",
        dedupeKey: "env-profile-name-conflict"
      });
      return;
    }

    pushToast({
      tone: "error",
      title,
      message: getErrorMessage(error),
      dedupeKey: options?.dedupeKey,
      action: options?.action
    });
  }

  async function refresh() {
    setIsRefreshing(true);

    try {
      const profileItems = await getJson<EnvProfile[]>("/v2/env-profiles");
      setItems(profileItems);
      onStatsChange({ profileCount: profileItems.length });
    } catch (error) {
      if (error instanceof ApiError && error.code === "ENV_PROFILE_NOT_CONFIGURED") {
        setItems([]);
        onStatsChange({ profileCount: 0 });
        pushToast({
          tone: "info",
          title: "未配置环境",
          message: "当前还没有环境配置，请先新增一个运行环境。",
          dedupeKey: "env-profiles-not-configured"
        });
        return;
      }
      notifyRequestError(error, "加载环境配置失败", {
        dedupeKey: "env-profiles-refresh",
        action: {
          label: "重试",
          onClick: () => {
            void refresh();
          }
        }
      });
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
    const isEditing = Boolean(editingId);

    try {
      if (isEditing) {
        await putJson(`/v2/env-profiles/${editingId}`, form);
      } else {
        await postJson("/v2/env-profiles", form);
      }
      setForm(initialForm);
      setEditingId("");
      pushToast({
        tone: "success",
        title: isEditing ? "更新成功" : "创建成功",
        message: isEditing ? "环境配置已更新。" : "环境配置已创建。",
        dedupeKey: isEditing ? "env-profile-update-success" : "env-profile-create-success"
      });
      await refresh();
    } catch (error) {
      notifyRequestError(error, isEditing ? "更新环境配置失败" : "创建环境配置失败", {
        dedupeKey: isEditing ? "env-profile-update-error" : "env-profile-create-error"
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleValidate(id: string) {
    setPendingValidationId(id);
    const profile = items.find((item) => item.id === id);
    const profileName = profile?.name || "目标环境";
    try {
      const result = await postJson<{ message: string }>(`/v2/env-profiles/${id}/validate`, {});
      setValidationById((current) => ({
        ...current,
        [id]: {
          status: "success",
          summary: result.message,
          checkedAt: formatCheckedAt()
        }
      }));
      pushToast({
        tone: "success",
        title: "校验完成",
        message: `${profileName}: ${result.message}`,
        dedupeKey: `env-profile-validate-success-${id}`
      });
    } catch (error) {
      const summary = getErrorMessage(error);
      setValidationById((current) => ({
        ...current,
        [id]: {
          status: "error",
          summary,
          checkedAt: formatCheckedAt()
        }
      }));
      notifyRequestError(error, "环境校验失败", {
        dedupeKey: `env-profile-validate-error-${id}`
      });
    } finally {
      setPendingValidationId("");
    }
  }

  async function handleEdit(id: string) {
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
      notifyRequestError(error, "加载环境详情失败", {
        dedupeKey: `env-profile-detail-${id}`
      });
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
            label={editingId ? "正在编辑" : isRefreshing ? "同步中" : "新增环境配置"}
            tone={editingId ? "warning" : "info"}
          />
        }
      />
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
            validationById={validationById}
            pendingValidationId={pendingValidationId}
            onEdit={(id) => void handleEdit(id)}
            onValidate={(id) => void handleValidate(id)}
          />
        </div>
      </div>
    </section>
  );
}
