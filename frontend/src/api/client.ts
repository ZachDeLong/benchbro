export type Backend = {
  name: string;
  url: string;
  status: string;
  models: string[];
};

export type BenchmarkInfo = {
  name: string;
  category: string;
  description: string;
  scoring_mode: string;
  estimated_runtime_minutes: number;
  dataset_size: number;
  stability: string;
  quant_sensitive: boolean;
  required_capabilities: string[];
};

export type Session = {
  id: number;
  model: string;
  preset: string | null;
  status: string;
  started_at: string;
  finished_at: string | null;
};

export type Run = {
  id: number;
  session_id: number;
  benchmark: string;
  status: string;
  score: number | null;
  runtime_seconds: number | null;
  subset_mode: string;
  started_at: string;
  finished_at: string | null;
};

export type SessionDetails = Session & {
  runs: Run[];
};

export type StartSessionConfig = {
  model: string;
  benchmarks: string[];
  subset?: string;
  preset?: string;
};

const BASE = "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function fetchHealth(): Promise<{ status: string }> {
  return request("/api/health");
}

export function fetchBackends(): Promise<Backend[]> {
  return request("/api/models/backends");
}

export function fetchBenchmarks(): Promise<BenchmarkInfo[]> {
  return request("/api/benchmarks");
}

export function fetchPresets(): Promise<Record<string, unknown>> {
  return request("/api/benchmarks/presets");
}

export function fetchSessions(): Promise<Session[]> {
  return request("/api/sessions");
}

export function fetchSession(id: number): Promise<SessionDetails> {
  return request(`/api/sessions/${id}`);
}

export function startSession(config: StartSessionConfig): Promise<{ session_id: number }> {
  return request("/api/sessions/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
}

export function fetchRunDetails(runId: number): Promise<Run> {
  return request(`/api/runs/${runId}/details`);
}
