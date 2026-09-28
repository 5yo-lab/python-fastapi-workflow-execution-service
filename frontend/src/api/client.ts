import type {
  ActionRecord,
  ApiError,
  HistoryEntry,
  Workflow,
  WorkflowAction,
  WorkflowSummary,
} from "../types/workflow";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    let error: ApiError;
    try {
      error = (await response.json()) as ApiError;
    } catch {
      error = {
        code: "HTTP_ERROR",
        message: `Request failed with status ${response.status}`,
      };
    }
    throw error;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function listWorkflows(): Promise<WorkflowSummary[]> {
  return request("/workflows");
}

export function getWorkflow(id: string): Promise<Workflow> {
  return request(`/workflows/${id}`);
}

export function getWorkflowHistory(id: string): Promise<HistoryEntry[]> {
  return request(`/workflows/${id}/history`);
}

export function getWorkflowActions(id: string): Promise<ActionRecord[]> {
  return request(`/workflows/${id}/actions`);
}

export function createWorkflow(
  reference: string,
  amount: number,
): Promise<Workflow> {
  return request("/workflows", {
    method: "POST",
    body: JSON.stringify({
      reference,
      payload: { customerId: "customer-1", amount },
    }),
  });
}

export function applyTransition(
  workflowId: string,
  action: WorkflowAction,
  expectedVersion: number,
): Promise<Workflow> {
  return request(`/workflows/${workflowId}/transitions`, {
    method: "POST",
    body: JSON.stringify({ action, expectedVersion }),
  });
}
