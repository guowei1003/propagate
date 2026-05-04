import type { AgentSpec, Profile, RunDetail, RunEvent, TaskDetail, TaskSummary } from "./types";

const API_PREFIX = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_PREFIX}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  listTasks: () => request<TaskSummary[]>("/tasks"),
  createTask: (payload: Record<string, unknown>) =>
    request<TaskDetail>("/tasks", { method: "POST", body: JSON.stringify(payload) }),
  getTask: (taskId: string) => request<TaskDetail>(`/tasks/${taskId}`),
  getRun: (taskId: string, runId: string) => request<RunDetail>(`/tasks/${taskId}/runs/${runId}`),
  getRunEvents: (taskId: string, runId: string) =>
    request<RunEvent[]>(`/tasks/${taskId}/runs/${runId}/events`),
  listAgents: () => request<AgentSpec[]>("/agents"),
  listProfiles: () => request<Profile[]>("/profiles"),
  createProfile: (payload: Record<string, unknown>) =>
    request<Profile>("/profiles", { method: "POST", body: JSON.stringify(payload) }),
  approveStep: (taskId: string, runId: string, payload: Record<string, unknown>) =>
    request(`/tasks/${taskId}/runs/${runId}/approve`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  rejectStep: (taskId: string, runId: string, payload: Record<string, unknown>) =>
    request(`/tasks/${taskId}/runs/${runId}/reject`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  resumeRun: (taskId: string, runId: string) =>
    request(`/tasks/${taskId}/runs/${runId}/resume`, { method: "POST" }),
};

export function subscribeToRunEvents(
  taskId: string,
  runId: string,
  onMessage: (event: MessageEvent<string>) => void,
) {
  const source = new EventSource(`${API_PREFIX}/tasks/${taskId}/runs/${runId}/stream`);
  source.onmessage = onMessage;
  return () => source.close();
}
