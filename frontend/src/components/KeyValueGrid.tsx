import type { ReactNode } from "react";

type KeyValueItem = {
  label: string;
  value: ReactNode;
};

type Props = {
  items: KeyValueItem[];
  columns?: 1 | 2;
};

export function KeyValueGrid({ items, columns = 2 }: Props) {
  return (
    <dl className={`key-value-grid key-value-grid--${columns}`}>
      {items.map((item) => (
        <div key={item.label} className="key-value-row">
          <dt>{item.label}</dt>
          <dd>{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
