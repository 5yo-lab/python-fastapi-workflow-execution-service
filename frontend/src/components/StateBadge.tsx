interface StateBadgeProps {
  state: string;
}

const STATE_CLASS: Record<string, string> = {
  CREATED: "badge-gray",
  VALIDATING: "badge-blue",
  PROCESSING: "badge-blue",
  APPROVED: "badge-yellow",
  COMPLETED: "badge-green",
  VALIDATION_FAILED: "badge-red",
  PROCESSING_FAILED: "badge-red",
  CANCELLED: "badge-red",
};

export function StateBadge({ state }: StateBadgeProps) {
  return (
    <span className={`badge ${STATE_CLASS[state] ?? "badge-gray"}`}>{state}</span>
  );
}
