import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchBackends, fetchSessions } from "../api/client";
import type { Backend, Session } from "../api/client";

function StatusDot({ status }: { status: string }) {
  const isReady = status === "ready";
  const isPartial = status === "partial";
  return (
    <span
      className={`inline-block w-2.5 h-2.5 rounded-full flex-shrink-0 ${
        isReady
          ? "bg-green-400"
          : isPartial
          ? "bg-yellow-400"
          : "bg-gray-600"
      }`}
    />
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: "bg-green-900 text-green-300",
    running: "bg-blue-900 text-blue-300",
    partial: "bg-yellow-900 text-yellow-300",
    failed: "bg-red-900 text-red-300",
  };
  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-medium ${
        colors[status] ?? "bg-gray-800 text-gray-400"
      }`}
    >
      {status}
    </span>
  );
}

export default function Home() {
  const [backends, setBackends] = useState<Backend[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchBackends(), fetchSessions()])
      .then(([b, s]) => {
        setBackends(b);
        setSessions(s);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 text-sm mt-1">
            LLM benchmark runner for local models
          </p>
        </div>
        <Link
          to="/new"
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          New Evaluation
        </Link>
      </div>

      {/* Backends */}
      <section>
        <h2 className="text-lg font-semibold text-gray-200 mb-3">
          Detected Backends
        </h2>
        {loading ? (
          <p className="text-gray-500 text-sm">Loading...</p>
        ) : backends.length === 0 ? (
          <div className="border border-gray-800 rounded-lg p-6 text-center">
            <p className="text-gray-500">No backends detected</p>
            <p className="text-gray-600 text-sm mt-1">
              Start Ollama, llama.cpp, or another OpenAI-compatible server
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {backends.map((b) => (
              <div
                key={b.name}
                className="bg-gray-900 border border-gray-800 rounded-lg p-4"
              >
                <div className="flex items-center gap-2 mb-2">
                  <StatusDot status={b.status} />
                  <span className="font-medium text-white text-sm">{b.name}</span>
                </div>
                <p className="text-gray-500 text-xs mb-2">{b.url}</p>
                {b.models.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {b.models.slice(0, 4).map((m) => (
                      <span
                        key={m}
                        className="px-1.5 py-0.5 bg-gray-800 text-gray-400 rounded text-xs"
                      >
                        {m}
                      </span>
                    ))}
                    {b.models.length > 4 && (
                      <span className="px-1.5 py-0.5 text-gray-600 text-xs">
                        +{b.models.length - 4} more
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Recent Sessions */}
      <section>
        <h2 className="text-lg font-semibold text-gray-200 mb-3">
          Recent Evaluations
        </h2>
        {loading ? (
          <p className="text-gray-500 text-sm">Loading...</p>
        ) : sessions.length === 0 ? (
          <div className="border border-gray-800 rounded-lg p-6 text-center">
            <p className="text-gray-500">No evaluations yet</p>
            <p className="text-gray-600 text-sm mt-1">
              Run your first benchmark to see results here
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {sessions.slice(0, 5).map((s) => (
              <Link
                key={s.id}
                to={`/results/${s.id}`}
                className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 hover:border-gray-700 hover:bg-gray-800 transition-colors"
              >
                <div>
                  <span className="text-sm font-medium text-white">
                    Session #{s.id}
                  </span>
                  {s.preset_used && (
                    <span className="ml-2 text-xs text-gray-500">
                      preset: {s.preset_used}
                    </span>
                  )}
                  <p className="text-xs text-gray-500 mt-0.5">
                    {new Date(s.started_at).toLocaleString()}
                  </p>
                </div>
                <StatusBadge status={s.status} />
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
