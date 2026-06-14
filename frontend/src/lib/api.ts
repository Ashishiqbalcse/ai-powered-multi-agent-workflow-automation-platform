export type TaskRun = {
  id: string;
  goal: string;
  status: string;
  budget_usd: number;
  cost_usd: number;
  max_iterations: number;
  iterations: number;
  plan_json: Record<string, unknown> | null;
  approval_payload: Record<string, unknown> | null;
  result_json: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  subtasks?: SubTask[];
  events?: AgentEvent[];
  api_calls?: ApiCall[];
};

export type SubTask = {
  id: string;
  run_id: string;
  agent_name: string;
  title: string;
  status: string;
  iteration: number;
  input_json: Record<string, unknown> | null;
  output_json: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
  updated_at: string;
};

export type AgentEvent = {
  id: string;
  run_id: string;
  agent_name: string;
  event_type: string;
  message: string;
  payload: Record<string, unknown> | null;
  created_at: string;
};

export type ApiCall = {
  id: string;
  run_id: string;
  agent_name: string;
  provider: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  created_at: string;
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function wsRunUrl(runId: string): string {
  const url = new URL(API_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `/api/v1/ws/runs/${runId}`;
  return url.toString();
}

export function createRun(goal: string, budgetUsd: number): Promise<TaskRun> {
  return request<TaskRun>("/api/v1/runs", {
    method: "POST",
    body: JSON.stringify({ goal, budget_usd: budgetUsd }),
  });
}

export function listRuns(): Promise<TaskRun[]> {
  return request<TaskRun[]>("/api/v1/runs");
}

export function getRun(runId: string): Promise<TaskRun> {
  return request<TaskRun>(`/api/v1/runs/${runId}`);
}

export function decideApproval(
  runId: string,
  approved: boolean,
  note?: string,
): Promise<TaskRun> {
  return request<TaskRun>(`/api/v1/runs/${runId}/approval`, {
    method: "POST",
    body: JSON.stringify({ approved, note }),
  });
}

