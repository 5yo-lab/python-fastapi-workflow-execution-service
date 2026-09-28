function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required env var: ${name}`);
  }
  return value;
}

export const config = {
  apiBaseUrl: process.env.API_BASE_URL ?? "http://localhost:8000",
  pollIntervalMs: Number(process.env.POLL_INTERVAL_MS ?? 2000),
  failureRate: Number(process.env.FAILURE_RATE ?? 0.15),
};
