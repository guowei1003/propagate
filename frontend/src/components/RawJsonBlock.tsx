type Props = {
  title: string;
  data: unknown;
};

export function RawJsonBlock({ title, data }: Props) {
  return (
    <details className="raw-json-block">
      <summary>{title}</summary>
      <pre>{JSON.stringify(data ?? {}, null, 2)}</pre>
    </details>
  );
}
