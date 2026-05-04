type Props = {
  status: string;
};

export function StatusBadge({ status }: Props) {
  return <span className={`status-badge status-badge--${status}`}>{status}</span>;
}
