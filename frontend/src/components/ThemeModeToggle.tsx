import type { ThemeMode } from "../lib/theme";

type Props = {
  mode: ThemeMode;
  onChange: (mode: ThemeMode) => void;
};

const options: Array<{ label: string; value: ThemeMode }> = [
  { label: "跟随系统", value: "system" },
  { label: "浅色", value: "light" },
  { label: "深色", value: "dark" }
];

export function ThemeModeToggle({ mode, onChange }: Props) {
  return (
    <div className="theme-toggle" role="group" aria-label="主题模式切换">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          className={mode === option.value ? "theme-toggle__button is-active" : "theme-toggle__button"}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
