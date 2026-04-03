export type RunEventPayload = {
  id: string;
  event_type: string;
  message: string;
};

export function subscribeRunEvents(runId: string, onMessage: (payload: RunEventPayload) => void): () => void {
  const source = new EventSource(`/v2/runs/${runId}/stream`);
  source.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data) as RunEventPayload);
    } catch {
      // Ignore malformed events to keep stream alive.
    }
  };
  return () => source.close();
}
