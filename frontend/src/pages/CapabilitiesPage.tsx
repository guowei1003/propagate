import { useEffect, useState } from "react";

import { CapabilityReviewList } from "../components/capabilities/CapabilityReviewList";
import { MetricStrip } from "../components/MetricStrip";
import { PageHeader } from "../components/PageHeader";
import { getErrorMessage, getJson, postJson } from "../lib/api";
import { buildCapabilityMetrics } from "../lib/presenters";

type Capability = { id: string; name: string; type: string; status: string; risk_score: number };

type Props = {
  meta: {
    eyebrow: string;
    title: string;
    description: string;
  };
  onStatsChange: (update: { taskCount?: number; profileCount?: number; pendingCapabilities?: number }) => void;
};

export function CapabilitiesPage({ meta, onStatsChange }: Props) {
  const [items, setItems] = useState<Capability[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pendingDecisionId, setPendingDecisionId] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function refresh() {
    setIsRefreshing(true);
    setErrorMessage("");

    try {
      const capabilityItems = await getJson<Capability[]>("/v2/capabilities");
      setItems(capabilityItems);
      onStatsChange({
        pendingCapabilities: capabilityItems.filter(
          (item) => !["approved", "rejected", "APPROVED", "REJECTED"].includes(item.status)
        ).length
      });
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsRefreshing(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleDecision(id: string, action: "approve" | "reject") {
    setPendingDecisionId(id);
    setErrorMessage("");
    try {
      await postJson(`/v2/capabilities/${id}/${action}`, { approver: "ui-user", comment: "" });
      await refresh();
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setPendingDecisionId("");
    }
  }

  return (
    <section className="page-section">
      <PageHeader eyebrow={meta.eyebrow} title={meta.title} description={meta.description} />
      {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}
      <MetricStrip items={buildCapabilityMetrics(items)} />
      <CapabilityReviewList
        items={items}
        pendingDecisionId={pendingDecisionId || (isRefreshing ? "refreshing" : "")}
        onDecision={(id, action) => void handleDecision(id, action)}
      />
    </section>
  );
}
