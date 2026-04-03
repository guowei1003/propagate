export function subscribeRunEvents(runId: string, onMessage: (payload: Record<string, unknown>) => void): () => void {
  const source = new EventSource(`/v2/runs/${runId}/stream`);
  source.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data) as Record<string, unknown>);
    } catch {
      // Ignore malformed events to keep stream alive.
    }
  };
  return () => source.close();
}
