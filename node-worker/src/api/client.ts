import { config } from "../config.js";
import type { ActionResultPayload, PendingAction } from "../types.js";

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`HTTP ${response.status}: ${body}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchPendingActions(): Promise<PendingAction[]> {
  const response = await fetch(`${config.apiBaseUrl}/actions/pending`);
  return parseJson<PendingAction[]>(response);
}

export async function claimAction(actionId: string): Promise<void> {
  const response = await fetch(
    `${config.apiBaseUrl}/actions/${actionId}/claim`,
    { method: "POST" },
  );
  await parseJson(response);
}

export async function reportResult(
  actionId: string,
  payload: ActionResultPayload,
): Promise<void> {
  const response = await fetch(
    `${config.apiBaseUrl}/actions/${actionId}/result`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  await parseJson(response);
}
