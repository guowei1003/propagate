import type { ThemeMode, ResolvedTheme } from "../lib/theme";
import { ThemeModeToggle } from "./ThemeModeToggle";

type Props = {
  eyebrow: string;
  title: string;
  description: string;
  themeMode: ThemeMode;
  resolvedTheme: ResolvedTheme;
  onThemeModeChange: (mode: ThemeMode) => void;
};

function getThemeLabel(mode: ThemeMode, resolvedTheme: ResolvedTheme): string {
  if (mode === "system") {
    return `跟随系统 · ${resolvedTheme === "dark" ? "深色" : "浅色"}`;
  }
  return mode === "dark" ? "深色" : "浅色";
}

export function ConsoleTopbar({
  eyebrow,
  title,
  description,
  themeMode,
  resolvedTheme,
  onThemeModeChange
}: Props) {
  return (
    <header className="console-topbar">
      <div className="console-topbar__context">
        <p className="console-topbar__path">
          <span>Propagate</span>
          <span>/</span>
          <strong>{title}</strong>
        </p>
        <div className="console-topbar__copy">
          <span className="console-topbar__eyebrow">{eyebrow}</span>
          <p className="console-topbar__description">{description}</p>
        </div>
      </div>
      <div className="console-topbar__actions">
        <span className="topbar-status">当前主题：{getThemeLabel(themeMode, resolvedTheme)}</span>
        <ThemeModeToggle mode={themeMode} onChange={onThemeModeChange} />
      </div>
    </header>
  );
}
