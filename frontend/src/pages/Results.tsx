import { useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchSession, cancelSession, fetchRunDetails } from "../api/client";
import type { SessionDetails, Run } from "../api/client";

type RunDetail = {
  id: number;
  question_index: number;
  prompt: string;
  raw_output: string;
  parsed_output: string;
  correct_answer: string;
  is_correct: boolean;
  latency_ms: number | null;
  token_count: number | null;
};

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: "bg-green-900 text-green-300",
    running: "bg-blue-900 text-blue-300 animate-pulse",
    partial: "bg-yellow-900 text-yellow-300",
    failed: "bg-red-900 text-red-300",
    cancelled: "bg-gray-700 text-gray-400",
    pending: "bg-gray-800 text-gray-400",
  };
  return (
    <span
      className={`px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${
        colors[status] ?? "bg-gray-800 text-gray-400"
      }`}
    >
      {status}
    </span>
  );
}

function ScoreDisplay({ run }: { run: Run }) {
  if (run.score === null) return <span className="text-gray-600">—</span>;

  if (run.benchmark_name.toLowerCase().includes("perplexity")) {
    return (
      <span className="text-2xl font-bold text-white">
        {run.score.toFixed(2)}
        <span className="text-sm text-gray-500 font-normal ml-1">ppl</span>
      </span>
    );
  }

  return (
    <span className="text-2xl font-bold text-white">
      {(run.score * 100).toFixed(1)}
      <span className="text-sm text-gray-500 font-normal ml-0.5">%</span>
    </span>
  );
}

function DetailPanel({ runId, onClose }: { runId: number; onClose: () => void }) {
  const [details, setDetails] = useState<RunDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "correct" | "wrong">("all");

  useEffect(() => {
    fetchRunDetails(runId)
      .then((d: unknown) => setDetails(d as RunDetail[]))
      .finally(() => setLoading(false));
  }, [runId]);

  const filtered = details.filter((d) => {
    if (filter === "correct") return d.is_correct;
    if (filter === "wrong") return !d.is_correct;
    return true;
  });

  const correct = details.filter((d) => d.is_correct).length;
  const wrong = details.length - correct;

  if (loading) return <p className="text-gray-500 text-sm py-4">Loading details...</p>;

  return (
    <div className="mt-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={() => setFilter("all")}
            className={`px-3 py-1 rounded text-xs font-medium ${
              filter === "all" ? "bg-gray-700 text-white" : "bg-gray-900 text-gray-400 hover:text-white"
            }`}
          >
            All ({details.length})
          </button>
          <button
            onClick={() => setFilter("correct")}
            className={`px-3 py-1 rounded text-xs font-medium ${
              filter === "correct" ? "bg-green-900 text-green-300" : "bg-gray-900 text-gray-400 hover:text-white"
            }`}
          >
            Correct ({correct})
          </button>
          <button
            onClick={() => setFilter("wrong")}
            className={`px-3 py-1 rounded text-xs font-medium ${
              filter === "wrong" ? "bg-red-900 text-red-300" : "bg-gray-900 text-gray-400 hover:text-white"
            }`}
          >
            Wrong ({wrong})
          </button>
        </div>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-white text-sm"
        >
          Close
        </button>
      </div>

      <div className="max-h-[600px] overflow-y-auto space-y-2">
        {filtered.map((d) => (
          <div
            key={d.id}
            className={`border rounded-lg p-3 text-sm ${
              d.is_correct
                ? "border-green-900/50 bg-green-950/20"
                : "border-red-900/50 bg-red-950/20"
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-500">Q#{d.question_index + 1}</span>
              <div className="flex items-center gap-2">
                {d.latency_ms !== null && (
                  <span className="text-xs text-gray-600">{(d.latency_ms / 1000).toFixed(1)}s</span>
                )}
                <span className={`text-xs font-medium ${d.is_correct ? "text-green-400" : "text-red-400"}`}>
                  {d.is_correct ? "CORRECT" : "WRONG"}
                </span>
              </div>
            </div>

            <details className="group">
              <summary className="cursor-pointer text-gray-400 hover:text-white text-xs mb-1">
                Show prompt
              </summary>
              <pre className="text-xs text-gray-500 bg-gray-950 rounded p-2 mt-1 whitespace-pre-wrap max-h-40 overflow-y-auto">
                {d.prompt}
              </pre>
            </details>

            <div className="mt-2">
              <p className="text-xs text-gray-500 mb-1">Model output:</p>
              <pre className="text-xs text-gray-300 bg-gray-950 rounded p-2 whitespace-pre-wrap max-h-40 overflow-y-auto">
                {d.raw_output}
              </pre>
            </div>

            <div className="mt-2 flex gap-4 text-xs">
              <span>
                <span className="text-gray-500">Parsed: </span>
                <span className="text-white font-mono">{d.parsed_output}</span>
              </span>
              <span>
                <span className="text-gray-500">Expected: </span>
                <span className="text-white font-mono">{d.correct_answer}</span>
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RunCard({ run }: { run: Run; }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <div className="flex items-start justify-between gap-2 mb-3">
        <span className="font-medium text-white">{run.benchmark_name}</span>
        <StatusBadge status={run.status} />
      </div>
      <div className="mb-2">
        <ScoreDisplay run={run} />
      </div>
      <div className="flex items-center justify-between">
        <div className="flex gap-4 text-xs text-gray-500">
          <span>subset: {run.subset_mode}</span>
          {run.runtime_seconds !== null && (
            <span>{run.runtime_seconds.toFixed(0)}s</span>
          )}
        </div>
        {run.status === "completed" && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-indigo-400 hover:text-indigo-300"
          >
            {expanded ? "Hide details" : "View details"}
          </button>
        )}
      </div>
      {expanded && <DetailPanel runId={run.id} onClose={() => setExpanded(false)} />}
    </div>
  );
}

export default function Results() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<SessionDetails | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function loadSession() {
    if (!id) return;
    fetchSession(Number(id))
      .then((d) => {
        setData(d);
        if (d.session.status !== "running" && d.session.status !== "pending") {
          if (intervalRef.current) clearInterval(intervalRef.current);
        }
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Failed to load session");
        if (intervalRef.current) clearInterval(intervalRef.current);
      });
  }

  useEffect(() => {
    loadSession();
    intervalRef.current = setInterval(loadSession, 3000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (error) {
    return (
      <div className="text-red-400 bg-red-950 border border-red-800 rounded-lg px-4 py-3 text-sm">
        {error}
      </div>
    );
  }

  if (!data) {
    return <p className="text-gray-500 text-sm">Loading session...</p>;
  }

  const session = data.session;
  const runs = data.runs;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-white">
              Session #{session.id}
            </h1>
            <StatusBadge status={session.status} />
          </div>
          <p className="text-gray-600 text-xs mt-0.5">
            Started {new Date(session.started_at).toLocaleString()}
            {session.completed_at && (
              <> · Finished {new Date(session.completed_at).toLocaleString()}</>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          {(session.status === "running" || session.status === "pending") && (
            <button
              onClick={async () => {
                await cancelSession(Number(id));
                loadSession();
              }}
              className="px-3 py-1.5 bg-red-900 hover:bg-red-800 text-red-300 rounded-lg text-sm transition-colors"
            >
              Cancel
            </button>
          )}
          <Link
            to="/new"
            className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm transition-colors"
          >
            New Eval
          </Link>
        </div>
      </div>

      {runs.length === 0 ? (
        <div className="border border-gray-800 rounded-lg p-6 text-center">
          <p className="text-gray-500">No benchmark runs yet</p>
          {session.status === "running" && (
            <p className="text-gray-600 text-sm mt-1">Polling for results...</p>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {runs.map((run) => (
            <RunCard key={run.id} run={run} />
          ))}
        </div>
      )}
    </div>
  );
}
