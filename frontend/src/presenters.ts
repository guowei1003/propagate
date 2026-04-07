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

export function getTaskStatusMeta(status: string): StatusMeta {
  const mapping: Record<string, StatusMeta> = {
    PENDING: { label: "待执行", tone: "info" },
    RUNNING: { label: "执行中", tone: "info" },
    COMPLETED: { label: "已完成", tone: "success" },
    FAILED: { label: "已失败", tone: "danger" }
  };
  return mapping[status] || { label: status || "未知", tone: "neutral" };
}

export function buildTaskMetrics(tasks: Array<{ status: string }>): MetricItem[] {
  const total = tasks.length;
  const running = tasks.filter((t) => t.status === "RUNNING").length;
  const completed = tasks.filter((t) => t.status === "COMPLETED").length;
  const failed = tasks.filter((t) => t.status === "FAILED").length;

  return [
    {
      label: "任务总数",
      value: formatCount(total),
      detail: "当前任务列表中的全部任务",
      tone: total > 0 ? "info" : "neutral"
    },
    {
      label: "执行中",
      value: formatCount(running),
      detail: "正在处理的任务",
      tone: running > 0 ? "info" : "neutral"
    },
    {
      label: "已完成",
      value: formatCount(completed),
      detail: "成功完成的任务",
      tone: completed > 0 ? "success" : "neutral"
    },
    {
      label: "已失败",
      value: formatCount(failed),
      detail: "执行失败的任务",
      tone: failed > 0 ? "danger" : "neutral"
    }
  ];
}

export function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return "刚刚";
  if (diffMin < 60) return `${diffMin} 分钟前`;
  if (diffHour < 24) return `${diffHour} 小时前`;
  if (diffDay < 30) return `${diffDay} 天前`;

  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  });
}

export function formatDuration(startIso: string, endIso: string | null): string {
  const start = new Date(startIso).getTime();
  const end = endIso ? new Date(endIso).getTime() : Date.now();
  const diffMs = end - start;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);

  if (diffSec < 60) return `${diffSec}s`;
  if (diffMin < 60) return `${diffMin}m ${diffSec % 60}s`;
  return `${diffHour}h ${diffMin % 60}m`;
}
