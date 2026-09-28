import type {
  ActionRecord,
  ApiError,
  HistoryEntry,
  Workflow,
  WorkflowAction,
} from "../types/workflow";
import {
  historyFromState,
  historyToState,
  workflowUpdatedAt,
} from "../types/workflow";
import { StateBadge } from "./StateBadge";
import { TransitionButtons } from "./TransitionButtons";

interface WorkflowDetailProps {
  workflow: Workflow | null;
  history: HistoryEntry[];
  actions: ActionRecord[];
  loading: boolean;
  onTransition: (action: WorkflowAction) => Promise<void>;
}

export function WorkflowDetail({
  workflow,
  history,
  actions,
  loading,
  onTransition,
}: WorkflowDetailProps) {
  if (!workflow) {
    return (
      <section className="card">
        <h2>Detail</h2>
        <p className="muted">Select a workflow to view details.</p>
      </section>
    );
  }

  return (
    <section className="card">
      <div className="detail-header">
        <h2>{workflow.reference}</h2>
        <StateBadge state={workflow.state} />
      </div>

      <dl className="meta-grid">
        <div>
          <dt>ID</dt>
          <dd>{workflow.id}</dd>
        </div>
        <div>
          <dt>Version</dt>
          <dd>{workflow.version}</dd>
        </div>
        <div>
          <dt>Correlation ID</dt>
          <dd>{workflow.correlation_id}</dd>
        </div>
        <div>
          <dt>Updated</dt>
          <dd>{new Date(workflowUpdatedAt(workflow)).toLocaleString()}</dd>
        </div>
      </dl>

      <h3>Payload</h3>
      <pre>{JSON.stringify(workflow.payload, null, 2)}</pre>

      <h3>Manual actions</h3>
      <TransitionButtons
        state={workflow.state}
        version={workflow.version}
        loading={loading}
        onTransition={(action) => void onTransition(action)}
      />

      <h3>Worker actions</h3>
      {actions.length === 0 ? (
        <p className="muted">No worker actions yet.</p>
      ) : (
        <table className="actions-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Status</th>
              <th>Attempt</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {actions.map((action) => (
              <tr key={action.id}>
                <td>{action.type}</td>
                <td>{action.status}</td>
                <td>
                  {action.attempt} / {action.maxAttempts ?? action.max_attempts}
                </td>
                <td>{action.error ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h3>History</h3>
      {history.length === 0 ? (
        <p className="muted">No transitions yet.</p>
      ) : (
        <ul className="timeline">
          {history.map((entry) => (
            <li key={entry.id}>
              <strong>{entry.action}</strong>: {historyFromState(entry)} →{" "}
              {historyToState(entry)}
              <span className="muted">
                {" "}
                · {new Date(entry.timestamp).toLocaleString()}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function ErrorAlert({ error }: { error: ApiError | null }) {
  if (!error) return null;

  return (
    <div className="alert" role="alert">
      <strong>{error.code}</strong>: {error.message}
    </div>
  );
}
