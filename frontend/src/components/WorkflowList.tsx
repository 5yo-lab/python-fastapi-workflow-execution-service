import type { WorkflowSummary } from "../types/workflow";
import { workflowUpdatedAt } from "../types/workflow";
import { StateBadge } from "./StateBadge";

interface WorkflowListProps {
  workflows: WorkflowSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function WorkflowList({
  workflows,
  selectedId,
  onSelect,
}: WorkflowListProps) {
  return (
    <section className="card">
      <h2>Workflows</h2>
      {workflows.length === 0 ? (
        <p className="muted">No workflows yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Reference</th>
              <th>State</th>
              <th>Version</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            {workflows.map((workflow) => (
              <tr
                key={workflow.id}
                className={workflow.id === selectedId ? "selected" : ""}
                onClick={() => onSelect(workflow.id)}
              >
                <td>{workflow.reference}</td>
                <td>
                  <StateBadge state={workflow.state} />
                </td>
                <td>{workflow.version}</td>
                <td>{new Date(workflowUpdatedAt(workflow)).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
