import { useEffect, useState } from "react";

import { getJson, postJson } from "../lib/api";

type TaskSummary = { id: string; title: string; run?: { id: string } | null };

export function ArtifactsPage() {
  const [artifacts, setArtifacts] = useState<Record<string, unknown> | null>(null);
  const [runId, setRunId] = useState("");

  useEffect(() => {
    void getJson<TaskSummary[]>("/v2/tasks").then(async (items) => {
      const latestRunId = items.find((item) => item.run?.id)?.run?.id;
      if (!latestRunId) {
        return;
      }
      setRunId(latestRunId);
      setArtifacts(await getJson(`/v2/runs/${latestRunId}/artifacts`));
    });
  }, []);

  async function handleBuildBundle() {
    if (!runId) return;
    await postJson(`/v2/runs/${runId}/bundle/build`, {});
    setArtifacts(await getJson(`/v2/runs/${runId}/bundle`));
  }

  return (
    <section className="panel">
      <h2>产物中心</h2>
      <div className="actions">
        <button type="button" onClick={() => void handleBuildBundle()}>
          构建 Bundle
        </button>
        {runId && (
          <a href={`/v2/runs/${runId}/bundle/download`} target="_blank" rel="noreferrer">
            下载 Bundle
          </a>
        )}
      </div>
      <pre>{JSON.stringify(artifacts, null, 2)}</pre>
    </section>
  );
}
