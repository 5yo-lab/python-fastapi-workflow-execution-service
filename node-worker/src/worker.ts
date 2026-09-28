import {
  claimAction,
  fetchPendingActions,
  reportResult,
} from "./api/client.js";
import { config } from "./config.js";
import { processProcess } from "./processors/process.js";
import { processValidate } from "./processors/validate.js";
import type { ActionResultPayload, PendingAction } from "./types.js";

function log(message: string, extra: Record<string, unknown> = {}): void {
  console.log(
    JSON.stringify({
      level: "info",
      message,
      timestamp: new Date().toISOString(),
      ...extra,
    }),
  );
}

async function processAction(action: PendingAction): Promise<void> {
  log("Processing action", {
    actionId: action.id,
    workflowId: action.workflowId,
    type: action.type,
    attempt: action.attempt,
  });

  await claimAction(action.id);

  let result: ActionResultPayload;
  if (action.type === "VALIDATE") {
    result = processValidate(action);
  } else {
    result = await processProcess(action);
  }

  await reportResult(action.id, result);

  log("Action completed", {
    actionId: action.id,
    workflowId: action.workflowId,
    type: action.type,
    success: result.success,
  });
}

async function pollOnce(): Promise<void> {
  const actions = await fetchPendingActions();

  for (const action of actions) {
    try {
      await processAction(action);
    } catch (error) {
      log("Action failed", {
        actionId: action.id,
        workflowId: action.workflowId,
        type: action.type,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }
}

export function startWorker(): void {
  log("Worker started", {
    apiBaseUrl: config.apiBaseUrl,
    pollIntervalMs: config.pollIntervalMs,
    failureRate: config.failureRate,
  });

  setInterval(() => {
    void pollOnce().catch((error) => {
      log("Poll failed", {
        error: error instanceof Error ? error.message : String(error),
      });
    });
  }, config.pollIntervalMs);
}
