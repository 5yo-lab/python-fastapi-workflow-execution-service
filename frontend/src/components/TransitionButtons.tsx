import type { WorkflowAction } from "../types/workflow";
import { MANUAL_ACTIONS_BY_STATE, TERMINAL_STATES } from "../types/workflow";

interface TransitionButtonsProps {
  state: string;
  version: number;
  loading: boolean;
  onTransition: (action: WorkflowAction) => void;
}

const ACTION_LABELS: Record<WorkflowAction, string> = {
  START_VALIDATION: "Start validation",
  START_PROCESSING: "Start processing",
  CANCEL: "Cancel",
};

export function TransitionButtons({
  state,
  version,
  loading,
  onTransition,
}: TransitionButtonsProps) {
  if (TERMINAL_STATES.has(state)) {
    return <p className="muted">No transitions available (terminal state).</p>;
  }

  const actions = MANUAL_ACTIONS_BY_STATE[state] ?? [];

  if (actions.length === 0) {
    return (
      <p className="muted">
        No manual actions while processing — waiting for worker.
      </p>
    );
  }

  return (
    <div className="button-row">
      {actions.map((action) => (
        <button
          key={action}
          type="button"
          disabled={loading}
          onClick={() => onTransition(action)}
          title={`Version ${version}`}
        >
          {ACTION_LABELS[action]}
        </button>
      ))}
    </div>
  );
}
