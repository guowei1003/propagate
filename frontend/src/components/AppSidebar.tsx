type SidebarView = {
  key: string;
  label: string;
};

type SidebarStats = {
  taskCount: number;
  profileCount: number;
  pendingCapabilities: number;
};

type Props = {
  currentViewLabel: string;
  pendingCapabilitiesLabel: string;
  stats: SidebarStats;
  view: string;
  views: SidebarView[];
  onChange: (view: string) => void;
};

function getCountLabel(key: string, stats: SidebarStats): string | null {
  if (key === "tasks") {
    return String(stats.taskCount);
  }
  if (key === "profiles") {
    return String(stats.profileCount);
  }
  if (key === "capabilities") {
    return String(stats.pendingCapabilities);
  }
  return null;
}

function getViewHint(key: string, active: boolean): string {
  if (active) {
    return "当前模块";
  }

  const hints: Record<string, string> = {
    tasks: "新建与检视任务",
    runs: "查看执行流",
    capabilities: "处理风险审批",
    profiles: "维护运行环境",
    artifacts: "交付与下载"
  };

  return hints[key] || "进入模块";
}

export function AppSidebar({ currentViewLabel, pendingCapabilitiesLabel, stats, view, views, onChange }: Props) {
  return (
    <aside className="sidebar-rail">
      <div className="sidebar-section sidebar-brand">
        <p className="brand-kicker">Propagate Console</p>
        <h1 className="brand-title">AI Task Operations</h1>
        <p className="brand-summary">以专业管理平台方式统一管理任务编排、执行监控、能力审批、环境配置与交付产物。</p>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-mini-label">系统摘要</div>
        <div className="sidebar-stat-list">
          <div className="sidebar-stat">
            <span>当前视图</span>
            <strong>{currentViewLabel}</strong>
          </div>
          <div className="sidebar-stat">
            <span>任务数</span>
            <strong>{stats.taskCount}</strong>
          </div>
          <div className="sidebar-stat">
            <span>环境数</span>
            <strong>{stats.profileCount}</strong>
          </div>
          <div className="sidebar-stat">
            <span>待审批</span>
            <strong>{pendingCapabilitiesLabel}</strong>
          </div>
        </div>
      </div>

      <nav className="sidebar-section sidebar-nav" aria-label="控制台导航">
        {views.map((item) => (
          <button
            key={item.key}
            className={item.key === view ? "sidebar-nav-button is-active" : "sidebar-nav-button"}
            onClick={() => onChange(item.key)}
            type="button"
          >
            <span className="sidebar-nav-button__topline">
              <span className="sidebar-nav-button__label">{item.label}</span>
              {getCountLabel(item.key, stats) ? (
                <span className="sidebar-nav-button__count">{getCountLabel(item.key, stats)}</span>
              ) : null}
            </span>
            <span className="sidebar-nav-button__hint">{getViewHint(item.key, item.key === view)}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-section sidebar-footnote">
        <span className="sidebar-mini-label">控制台状态</span>
        <p>当前聚焦：{currentViewLabel}，待审批能力：{pendingCapabilitiesLabel}。</p>
      </div>
    </aside>
  );
}
