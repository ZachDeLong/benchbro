import { useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchSession } from "../api/client";
import type { SessionDetails, Run } from "../api/client";

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: "bg-green-900 text-green-300",
    running: "bg-blue-900 text-blue-300 animate-pulse",
    partial: "bg-yellow-900 text-yellow-300",
    failed: "bg-red-900 text-red-300",
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

  // Perplexity: lower is better, show as raw number
  if (run.benchmark.toLowerCase().includes("perplexity")) {
    return (
      <span className="text-2xl font-bold text-white">
        {run.score.toFixed(2)}
        <span className="text-sm text-gray-500 font-normal ml-1">ppl</span>
      </span>
    );
  }

  // Everything else: percentage
  return (
    <span className="text-2xl font-bold text-white">
      {(run.score * 100).toFixed(1)}
      <span className="text-sm text-gray-500 font-normal ml-0.5">%</span>
    </span>
  );
}

function RunCard({ run }: { run: Run }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <div className="flex items-start justify-between gap-2 mb-3">
        <span className="font-medium text-white">{run.benchmark}</span>
        <StatusBadge status={run.status} />
      </div>
      <div className="mb-2">
        <ScoreDisplay run={run} />
      </div>
      <div className="flex gap-4 text-xs text-gray-500">
        <span>subset: {run.subset_mode}</span>
        {run.runtime_seconds !== null && (
          <span>{run.runtime_seconds.toFixed(0)}s</span>
        )}
      </div>
    </div>
  );
}

export default function Results() {
  const { id } = useParams<{ id: string }>();
  const [session, setSession] = useState<SessionDetails | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function loadSession() {
    if (!id) return;
    fetchSession(Number(id))
      .then((s) => {
        setSession(s);
        if (s.status !== "running" && s.status !== "pending") {
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

  if (!session) {
    return <p className="text-gray-500 text-sm">Loading session...</p>;
  }

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
          <p className="text-gray-400 text-sm">{session.model}</p>
          <p className="text-gray-600 text-xs mt-0.5">
            Started {new Date(session.started_at).toLocaleString()}
            {session.finished_at && (
              <> · Finished {new Date(session.finished_at).toLocaleString()}</>
            )}
          </p>
        </div>
        <Link
          to="/new"
          className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm transition-colors"
        >
          New Eval
        </Link>
      </div>

      {session.runs.length === 0 ? (
        <div className="border border-gray-800 rounded-lg p-6 text-center">
          <p className="text-gray-500">No benchmark runs yet</p>
          {session.status === "running" && (
            <p className="text-gray-600 text-sm mt-1">Polling for results...</p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {session.runs.map((run) => (
            <RunCard key={run.id} run={run} />
          ))}
        </div>
      )}
    </div>
  );
}
