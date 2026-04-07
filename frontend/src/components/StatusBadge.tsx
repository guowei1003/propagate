import type { Tone } from "../presenters";

type Props = {
  label: string;
  tone: Tone;
};

export function StatusBadge({ label, tone }: Props) {
  return <span className={`status-badge status-badge--${tone}`}>{label}</span>;
}
