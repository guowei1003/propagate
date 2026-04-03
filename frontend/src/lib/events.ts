export type RunEventPayload = {
  id: string;
  event_type: string;
  message: string;
};

export type TimelineEvent = {
  id: string;
  title: string;
  description: string;
  meta: string;
};

export function normalizeRunEvent(payload: Partial<RunEventPayload>, index: number): RunEventPayload {
  return {
    id: payload.id || `run-event-${index + 1}`,
    event_type: payload.event_type || "运行事件",
    message: payload.message || "收到新的执行事件。"
  };
}

export function buildTimelineEvent(payload: Partial<RunEventPayload>, index: number): TimelineEvent {
  const event = normalizeRunEvent(payload, index);
  return {
    id: event.id,
    title: event.event_type,
    description: event.message,
    meta: `事件 #${index + 1}`
  };
}

export function subscribeRunEvents(runId: string, onMessage: (payload: RunEventPayload) => void): () => void {
  const source = new EventSource(`/v2/runs/${runId}/stream`);
  source.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data) as Partial<RunEventPayload>;
      onMessage(normalizeRunEvent(payload, Date.now()));
    } catch {
      // Ignore malformed events to keep stream alive.
    }
  };
  return () => source.close();
}
