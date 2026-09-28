import { config } from "../config.js";
import type { ActionResultPayload, PendingAction } from "../types.js";

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function randomMs(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

export async function processProcess(
  _action: PendingAction,
): Promise<ActionResultPayload> {
  await sleep(randomMs(500, 1500));

  if (Math.random() < config.failureRate) {
    return { success: false, error: "Simulated processing error" };
  }

  return { success: true, result: { processed: true } };
}
