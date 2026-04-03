export type Tone = "neutral" | "info" | "success" | "warning" | "danger";

export type StatusMeta = {
  label: string;
  tone: Tone;
};

export type MetricItem = {
  label: string;
  value: string;
  detail: string;
  tone: Tone;
};

const numberFormatter = new Intl.NumberFormat("zh-CN");

function formatCount(value: number): string {
  return numberFormatter.format(value);
}

export function formatBooleanLabel(value: boolean): string {
  return value ? "已启用" : "已关闭";
}

export function getTaskStatusMeta(status: string): StatusMeta {
  const mapping: Record<string, StatusMeta> = {
    CREATED: { label: "已创建", tone: "info" },
    WAITING_USER_INPUT: { label: "等待补充", tone: "warning" },
    WAITING_APPROVAL: { label: "等待审批", tone: "warning" },
    RUNNING: { label: "执行中", tone: "info" },
    COMPLETED: { label: "已完成", tone: "success" },
    PARTIAL_SUCCESS: { label: "部分完成", tone: "warning" },
    FAILED: { label: "已失败", tone: "danger" }
  };
  return mapping[status] || { label: status || "未知状态", tone: "neutral" };
}

export function getPhaseLabel(phase: string): string {
  const mapping: Record<string, string> = {
    REQUIREMENT_ANALYZING: "需求分析",
    TASK_DECOMPOSING: "任务拆解",
    TASK_EVALUATING: "策略评估",
    SUBTASK_RUNNING: "子任务执行",
    REPORTING: "报告生成"
  };
  return mapping[phase] || phase || "未进入阶段";
}

export function getSubtaskStatusMeta(status: string): StatusMeta {
  const mapping: Record<string, StatusMeta> = {
    PENDING: { label: "待执行", tone: "neutral" },
    READY: { label: "已就绪", tone: "info" },
    RUNNING: { label: "执行中", tone: "info" },
    RETRY_PENDING: { label: "待重试", tone: "warning" },
    COMPLETED: { label: "已完成", tone: "success" },
    NEEDS_HUMAN_REVIEW: { label: "需人工介入", tone: "danger" }
  };
  return mapping[status] || { label: status || "未知状态", tone: "neutral" };
}

export function getProviderLabel(providerType: string): string {
  const mapping: Record<string, string> = {
    demo: "Demo 模式",
    openai_compatible: "兼容 OpenAI"
  };
  return mapping[providerType] || providerType || "未配置";
}

export function getRiskLevelMeta(riskScore: number): StatusMeta {
  if (riskScore >= 71) {
    return { label: "高风险", tone: "danger" };
  }
  if (riskScore >= 31) {
    return { label: "中风险", tone: "warning" };
  }
  return { label: "低风险", tone: "success" };
}

export function buildTaskMetrics(
  tasks: Array<{ status: string }>,
  profiles: Array<unknown>,
  selectedTask?: { current_phase?: string } | null
): MetricItem[] {
  const waitingInputCount = tasks.filter((task) => task.status === "WAITING_USER_INPUT").length;
  const runningCount = tasks.filter((task) => task.status === "RUNNING").length;
  return [
    {
      label: "任务总数",
      value: formatCount(tasks.length),
      detail: "当前已进入控制台的任务",
      tone: "info"
    },
    {
      label: "待补充",
      value: formatCount(waitingInputCount),
      detail: "等待澄清答复",
      tone: waitingInputCount > 0 ? "warning" : "neutral"
    },
    {
      label: "活跃任务",
      value: formatCount(runningCount),
      detail: selectedTask?.current_phase ? `当前阶段：${getPhaseLabel(selectedTask.current_phase)}` : "查看执行链路推进状态",
      tone: runningCount > 0 ? "info" : "neutral"
    },
    {
      label: "可用环境",
      value: formatCount(profiles.length),
      detail: "当前可选运行配置",
      tone: profiles.length > 0 ? "success" : "warning"
    }
  ];
}

export function buildRunMetrics(
  items: Array<{ run?: { status: string } | null; events?: Array<unknown>; dependencies?: Array<unknown> }>,
  activeItem?: { events?: Array<unknown>; dependencies?: Array<unknown> } | null
): MetricItem[] {
  const runs = items.filter((item) => item.run?.status);
  const runningCount = runs.filter((item) => item.run?.status === "RUNNING").length;
  const dependencyCount = activeItem?.dependencies?.length || 0;
  const eventCount = activeItem?.events?.length || 0;

  return [
    {
      label: "活跃运行",
      value: formatCount(runs.length),
      detail: "当前可订阅的运行实例",
      tone: runs.length > 0 ? "info" : "neutral"
    },
    {
      label: "执行中",
      value: formatCount(runningCount),
      detail: "仍在推进中的执行链路",
      tone: runningCount > 0 ? "info" : "neutral"
    },
    {
      label: "依赖关系",
      value: formatCount(dependencyCount),
      detail: "当前运行中的前后置节点",
      tone: dependencyCount > 0 ? "warning" : "success"
    },
    {
      label: "事件条目",
      value: formatCount(eventCount),
      detail: "用于追踪推进的事件流",
      tone: eventCount > 0 ? "success" : "neutral"
    }
  ];
}

export function buildCapabilityMetrics(items: Array<{ risk_score: number; status: string }>): MetricItem[] {
  const highRisk = items.filter((item) => item.risk_score >= 71).length;
  const pending = items.filter((item) => !["approved", "rejected", "APPROVED", "REJECTED"].includes(item.status)).length;
  const approved = items.filter((item) => ["approved", "APPROVED"].includes(item.status)).length;

  return [
    {
      label: "审批总数",
      value: formatCount(items.length),
      detail: "当前能力审批记录",
      tone: items.length > 0 ? "info" : "neutral"
    },
    {
      label: "高风险",
      value: formatCount(highRisk),
      detail: "需要优先关注的能力项",
      tone: highRisk > 0 ? "danger" : "success"
    },
    {
      label: "待决策",
      value: formatCount(pending),
      detail: "仍需人工决策",
      tone: pending > 0 ? "warning" : "success"
    },
    {
      label: "已通过",
      value: formatCount(approved),
      detail: "已允许进入执行链路",
      tone: approved > 0 ? "success" : "neutral"
    }
  ];
}

export function buildProfileMetrics(
  items: Array<{ provider_type: string }>,
  editingId: string
): MetricItem[] {
  const demoCount = items.filter((item) => item.provider_type === "demo").length;
  const compatibleCount = items.filter((item) => item.provider_type === "openai_compatible").length;

  return [
    {
      label: "可用环境",
      value: formatCount(items.length),
      detail: "当前可供编排调用的环境",
      tone: items.length > 0 ? "info" : "warning"
    },
    {
      label: "Demo 模式",
      value: formatCount(demoCount),
      detail: "适合调试流程",
      tone: demoCount > 0 ? "neutral" : "warning"
    },
    {
      label: "兼容 OpenAI",
      value: formatCount(compatibleCount),
      detail: "可接入外部模型服务",
      tone: compatibleCount > 0 ? "success" : "neutral"
    },
    {
      label: "表单状态",
      value: editingId ? "进行中" : "新建模式",
      detail: editingId ? "当前表单已载入环境配置" : "当前处于新增环境模式",
      tone: editingId ? "warning" : "info"
    }
  ];
}

export function buildArtifactMetrics(payload: {
  runId: string;
  artifacts: Record<string, unknown> | null;
  isBuilding: boolean;
}): MetricItem[] {
  const artifactCount = payload.artifacts ? Object.keys(payload.artifacts).length : 0;

  return [
    {
      label: "最近 Run",
      value: payload.runId || "暂无",
      detail: payload.runId ? "当前页面聚焦的运行编号" : "当前还没有可交付运行",
      tone: payload.runId ? "info" : "neutral"
    },
    {
      label: "产物字段",
      value: formatCount(artifactCount),
      detail: "当前已加载的产物摘要字段",
      tone: artifactCount > 0 ? "success" : "neutral"
    },
    {
      label: "Bundle 状态",
      value: payload.isBuilding ? "构建中" : payload.runId ? "可操作" : "等待运行",
      detail: payload.isBuilding ? "正在生成 Bundle 产物" : "可以继续构建或下载",
      tone: payload.isBuilding ? "warning" : payload.runId ? "info" : "neutral"
    },
    {
      label: "交付准备度",
      value: artifactCount > 0 ? "已生成摘要" : "待生成",
      detail: artifactCount > 0 ? "当前页面已有基础交付信息" : "请先完成一次运行或构建 Bundle",
      tone: artifactCount > 0 ? "success" : "warning"
    }
  ];
}
