import { FormEvent, useState } from "react";

interface CreateWorkflowFormProps {
  onCreate: (reference: string, amount: number) => Promise<void>;
}

export function CreateWorkflowForm({ onCreate }: CreateWorkflowFormProps) {
  const [reference, setReference] = useState("");
  const [amount, setAmount] = useState("100");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    try {
      await onCreate(reference.trim(), Number(amount));
      setReference("");
      setAmount("100");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="card" onSubmit={(event) => void handleSubmit(event)}>
      <h2>Create workflow</h2>
      <label>
        Reference
        <input
          value={reference}
          onChange={(event) => setReference(event.target.value)}
          placeholder="WF-001"
          required
        />
      </label>
      <label>
        Amount
        <input
          type="number"
          step="0.01"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          required
        />
      </label>
      <button type="submit" disabled={submitting}>
        {submitting ? "Creating…" : "Create"}
      </button>
    </form>
  );
}
