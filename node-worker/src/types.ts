export interface PendingAction {
  id: string;
  workflowId: string;
  type: "VALIDATE" | "PROCESS";
  status: string;
  attempt: number;
  maxAttempts: number;
  payload: {
    customerId?: string;
    amount?: number;
  };
  createdAt: string;
}

export interface ActionResultPayload {
  success: boolean;
  result?: Record<string, unknown>;
  error?: string;
}
