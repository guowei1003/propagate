type Props = {
  mission: Record<string, unknown> | null;
};

export function MissionPanel({ mission }: Props) {
  const success = (mission?.success_criteria as string[] | undefined) ?? [];
  const constraints = (mission?.constraints as string[] | undefined) ?? [];
  const deliverables = (mission?.deliverables as string[] | undefined) ?? [];

  return (
    <section className="card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Mission</p>
          <h3>{String(mission?.goal ?? "等待 mission 生成")}</h3>
        </div>
      </div>
      <div className="grid three">
        <div>
          <h4>成功标准</h4>
          <ul>{success.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
        <div>
          <h4>约束</h4>
          <ul>{constraints.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
        <div>
          <h4>交付物</h4>
          <ul>{deliverables.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      </div>
    </section>
  );
}
