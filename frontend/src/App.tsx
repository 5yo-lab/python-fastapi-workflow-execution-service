import { useCallback, useState } from "react";
import {
  applyTransition,
  createWorkflow,
  getWorkflow,
  getWorkflowActions,
  getWorkflowHistory,
  listWorkflows,
} from "./api/client";
import { CreateWorkflowForm } from "./components/CreateWorkflowForm";
import { ErrorAlert, WorkflowDetail } from "./components/WorkflowDetail";
import { WorkflowList } from "./components/WorkflowList";
import { usePolling } from "./hooks/usePolling";
import type {
  ActionRecord,
  ApiError,
  HistoryEntry,
  Workflow,
  WorkflowAction,
  WorkflowSummary,
} from "./types/workflow";

const POLL_INTERVAL_MS = 3000;

export default function App() {
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [actions, setActions] = useState<ActionRecord[]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const items = await listWorkflows();
      setWorkflows(items);

      if (selectedId) {
        const [workflow, workflowHistory, workflowActions] = await Promise.all([
          getWorkflow(selectedId),
          getWorkflowHistory(selectedId),
          getWorkflowActions(selectedId),
        ]);
        setSelectedWorkflow(workflow);
        setHistory(workflowHistory);
        setActions(workflowActions);
      }
    } catch (err) {
      setError(err as ApiError);
    }
  }, [selectedId]);

  usePolling(refresh, POLL_INTERVAL_MS);

  async function handleCreate(reference: string, amount: number) {
    setError(null);
    try {
      const workflow = await createWorkflow(reference, amount);
      setSelectedId(workflow.id);
      await refresh();
    } catch (err) {
      setError(err as ApiError);
    }
  }

  async function handleSelect(id: string) {
    setSelectedId(id);
    setError(null);
    try {
      const [workflow, workflowHistory, workflowActions] = await Promise.all([
        getWorkflow(id),
        getWorkflowHistory(id),
        getWorkflowActions(id),
      ]);
      setSelectedWorkflow(workflow);
      setHistory(workflowHistory);
      setActions(workflowActions);
    } catch (err) {
      setError(err as ApiError);
    }
  }

  async function handleTransition(action: WorkflowAction) {
    if (!selectedWorkflow) return;

    setLoading(true);
    setError(null);
    try {
      const updated = await applyTransition(
        selectedWorkflow.id,
        action,
        selectedWorkflow.version,
      );
      setSelectedWorkflow(updated);
      await refresh();
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>Workflow Control Panel</h1>
        <p className="muted">Polling every {POLL_INTERVAL_MS / 1000}s</p>
      </header>

      <ErrorAlert error={error} />

      <div className="layout">
        <div className="sidebar">
          <CreateWorkflowForm onCreate={handleCreate} />
          <WorkflowList
            workflows={workflows}
            selectedId={selectedId}
            onSelect={(id) => void handleSelect(id)}
          />
        </div>
        <WorkflowDetail
          workflow={selectedWorkflow}
          history={history}
          actions={actions}
          loading={loading}
          onTransition={handleTransition}
        />
      </div>
    </div>
  );
}
