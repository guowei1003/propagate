import { useEffect, useState } from "react";

import { getJson, postJson } from "../lib/api";

type Capability = { id: string; name: string; type: string; status: string; risk_score: number };

export function CapabilitiesPage() {
  const [items, setItems] = useState<Capability[]>([]);

  async function refresh() {
    setItems(await getJson<Capability[]>("/v2/capabilities"));
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleDecision(id: string, action: "approve" | "reject") {
    await postJson(`/v2/capabilities/${id}/${action}`, { approver: "ui-user", comment: "" });
    await refresh();
  }

  return (
    <section className="panel">
      <h2>能力中心</h2>
      <div className="stack">
        {items.map((item) => (
          <div key={item.id} className="card">
            <strong>{item.name}</strong>
            <span>Type: {item.type}</span>
            <span>Status: {item.status}</span>
            <span>Risk: {item.risk_score}</span>
            <div className="actions">
              <button type="button" onClick={() => void handleDecision(item.id, "approve")}>
                审批通过
              </button>
              <button type="button" onClick={() => void handleDecision(item.id, "reject")}>
                驳回
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
