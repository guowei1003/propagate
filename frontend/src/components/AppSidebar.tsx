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

export function AppSidebar({ currentViewLabel, pendingCapabilitiesLabel, stats, view, views, onChange }: Props) {
  return (
    <aside className="sidebar-rail">
      <div className="sidebar-section">
        <p className="brand-kicker">Propagate</p>
        <h1 className="brand-title">AI Execution Control Center</h1>
        <p className="brand-summary">用统一的调度台收敛任务编排、运行审查、能力审批、环境配置与交付产物。</p>
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
            <span className="sidebar-nav-button__label">{item.label}</span>
            <span className="sidebar-nav-button__hint">{item.key === view ? "当前视图" : "进入模块"}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-section sidebar-footnote">
        <span className="sidebar-mini-label">控制台状态</span>
        <p>默认态也必须可读、可操作、可交付。</p>
      </div>
    </aside>
  );
}
