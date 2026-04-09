import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchSessions } from "../api/client";
import type { Session } from "../api/client";
import StatusBadge from "../components/StatusBadge";

export default function History() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSessions()
      .then(setSessions)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Evaluation History</h1>
        <p className="text-gray-400 text-sm mt-1">All past benchmark sessions</p>
      </div>

      {loading ? (
        <p className="text-gray-500 text-sm">Loading...</p>
      ) : sessions.length === 0 ? (
        <div className="border border-gray-800 rounded-lg p-6 text-center">
          <p className="text-gray-500">No evaluations yet</p>
          <Link
            to="/new"
            className="inline-block mt-3 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Run your first evaluation
          </Link>
        </div>
      ) : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <Link
              key={s.id}
              to={`/results/${s.id}`}
              className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 hover:border-gray-700 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-4">
                <span className="text-gray-600 text-sm font-mono">#{s.id}</span>
                <div>
                  <span className="text-sm font-medium text-white">
                    {s.model_name}
                  </span>
                  <span className="ml-2 text-xs text-gray-600">
                    {s.backend_type}
                  </span>
                  {s.preset_used && (
                    <span className="ml-2 text-xs text-gray-500">
                      {s.preset_used}
                    </span>
                  )}
                  <p className="text-xs text-gray-500 mt-0.5">
                    {new Date(s.started_at).toLocaleString()}
                  </p>
                </div>
              </div>
              <StatusBadge status={s.status} />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
