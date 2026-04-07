import { useState, useEffect, useCallback } from "react";
import type { ThemeMode } from "../theme";
import {
  getStoredThemeMode,
  getSystemTheme,
  resolveTheme,
  applyThemeToDocument,
  persistThemeMode
} from "../theme";

export function ThemeToggle() {
  const [mode, setMode] = useState<ThemeMode>(() => getStoredThemeMode());
  const systemTheme = getSystemTheme();
  const resolved = resolveTheme(mode, systemTheme);

  useEffect(() => {
    applyThemeToDocument(resolved);
  }, [resolved]);

  const cycleTheme = useCallback(() => {
    const next: ThemeMode = mode === "system" ? "light" : mode === "light" ? "dark" : "system";
    setMode(next);
    persistThemeMode(next);
  }, [mode]);

  const themeIcon = resolved === "dark" ? (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  ) : (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1" x2="12" y2="3" />
      <line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1" y1="12" x2="3" y2="12" />
      <line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  );

  return (
    <div className="theme-toggle">
      <button
        className={`theme-toggle__button ${resolved === "dark" ? "is-active" : ""}`}
        onClick={cycleTheme}
        title={`当前主题: ${resolved === "dark" ? "深色" : "浅色"}，点击切换`}
        aria-label="Toggle theme"
      >
        {themeIcon}
      </button>
    </div>
  );
}
