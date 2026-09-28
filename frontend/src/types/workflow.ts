export type WorkflowAction =
  | "START_VALIDATION"
  | "START_PROCESSING"
  | "CANCEL";

export interface WorkflowSummary {
  id: string;
  reference: string;
  state: string;
  version: number;
  updatedAt?: string;
  updated_at?: string;
}

export interface Workflow extends WorkflowSummary {
  payload: Record<string, unknown>;
  correlation_id: string;
  created_at: string;
}

export interface HistoryEntry {
  id: string;
  fromState?: string;
  from_state?: string;
  toState?: string;
  to_state?: string;
  action: string;
  correlationId?: string;
  correlation_id?: string;
  timestamp: string;
}

export interface ActionRecord {
  id: string;
  workflowId?: string;
  workflow_id?: string;
  type: string;
  status: string;
  attempt: number;
  maxAttempts?: number;
  max_attempts?: number;
  error?: string | null;
  createdAt?: string;
  created_at?: string;
  completedAt?: string | null;
  completed_at?: string | null;
}

export interface ApiError {
  code: string;
  message: string;
}

export const MANUAL_ACTIONS_BY_STATE: Record<string, WorkflowAction[]> = {
  CREATED: ["START_VALIDATION", "CANCEL"],
  VALIDATING: ["CANCEL"],
  APPROVED: ["START_PROCESSING", "CANCEL"],
};

export const TERMINAL_STATES = new Set([
  "VALIDATION_FAILED",
  "PROCESSING_FAILED",
  "COMPLETED",
  "CANCELLED",
]);

export function workflowUpdatedAt(workflow: WorkflowSummary): string {
  return workflow.updatedAt ?? workflow.updated_at ?? "";
}

export function historyFromState(entry: HistoryEntry): string {
  return entry.fromState ?? entry.from_state ?? "";
}

export function historyToState(entry: HistoryEntry): string {
  return entry.toState ?? entry.to_state ?? "";
}
