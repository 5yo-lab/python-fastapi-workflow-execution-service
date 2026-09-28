import type { ActionResultPayload, PendingAction } from "../types.js";

export function processValidate(action: PendingAction): ActionResultPayload {
  const amount = action.payload.amount ?? 0;

  if (amount > 0) {
    return { success: true, result: { validated: true } };
  }

  return { success: false, error: "Amount must be positive" };
}
