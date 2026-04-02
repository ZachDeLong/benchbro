import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchBackends, fetchBenchmarks, startSession } from "../api/client";
import type { Backend, BenchmarkInfo } from "../api/client";

const SUBSET_OPTIONS = [
  { value: "full", label: "Full dataset" },
  { value: "25pct", label: "25% sample" },
  { value: "10pct", label: "10% sample" },
];

function CategoryTag({ category }: { category: string }) {
  const colors: Record<string, string> = {
    math: "bg-purple-900 text-purple-300",
    reasoning: "bg-blue-900 text-blue-300",
    coding: "bg-green-900 text-green-300",
    knowledge: "bg-orange-900 text-orange-300",
    language: "bg-pink-900 text-pink-300",
  };
  return (
    <span
      className={`px-1.5 py-0.5 rounded text-xs font-medium ${
        colors[category.toLowerCase()] ?? "bg-gray-800 text-gray-400"
      }`}
    >
      {category}
    </span>
  );
}

export default function NewEval() {
  const navigate = useNavigate();
  const [backends, setBackends] = useState<Backend[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [selectedBenchmarks, setSelectedBenchmarks] = useState<Set<string>>(new Set());
  const [subset, setSubset] = useState("full");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchBackends(), fetchBenchmarks()])
      .then(([b, bm]) => {
        setBackends(b);
        setBenchmarks(bm);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const allModels = backends.flatMap((b) =>
    b.models.map((m) => ({ backend: b.name, model: m }))
  );

  function toggleBenchmark(name: string) {
    setSelectedBenchmarks((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  async function handleRun() {
    if (!selectedModel || selectedBenchmarks.size === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await startSession({
        model: selectedModel,
        benchmarks: Array.from(selectedBenchmarks),
        subset,
      });
      navigate(`/results/${result.session_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start session");
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="text-gray-500 text-sm">Loading backends and benchmarks...</div>
    );
  }

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">New Evaluation</h1>
        <p className="text-gray-400 text-sm mt-1">
          Select a model and benchmarks to run
        </p>
      </div>

      {/* Step 1: Model */}
      <section>
        <h2 className="text-base font-semibold text-gray-200 mb-3">
          1. Select Model
        </h2>
        {allModels.length === 0 ? (
          <p className="text-gray-500 text-sm">
            No models found. Make sure a backend is running.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {allModels.map(({ backend, model }) => {
              const key = model;
              const isSelected = selectedModel === key;
              return (
                <button
                  key={`${backend}::${model}`}
                  onClick={() => setSelectedModel(isSelected ? null : key)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium border transition-colors ${
                    isSelected
                      ? "bg-indigo-600 border-indigo-500 text-white"
                      : "bg-gray-900 border-gray-700 text-gray-300 hover:border-gray-500 hover:text-white"
                  }`}
                >
                  {model}
                  <span className="ml-1.5 text-xs opacity-60">{backend}</span>
                </button>
              );
            })}
          </div>
        )}
      </section>

      {/* Step 2: Benchmarks */}
      <section>
        <h2 className="text-base font-semibold text-gray-200 mb-3">
          2. Select Benchmarks
        </h2>
        {benchmarks.length === 0 ? (
          <p className="text-gray-500 text-sm">No benchmarks available.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {benchmarks.map((bm) => {
              const isSelected = selectedBenchmarks.has(bm.name);
              return (
                <button
                  key={bm.name}
                  onClick={() => toggleBenchmark(bm.name)}
                  className={`text-left p-4 rounded-lg border transition-colors ${
                    isSelected
                      ? "bg-indigo-950 border-indigo-600"
                      : "bg-gray-900 border-gray-800 hover:border-gray-600"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span className="font-medium text-white text-sm">{bm.name}</span>
                    <div className="flex gap-1 flex-shrink-0">
                      <CategoryTag category={bm.category} />
                      {bm.quant_sensitive && (
                        <span className="px-1.5 py-0.5 bg-red-950 text-red-400 rounded text-xs font-medium">
                          quant
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-gray-400 text-xs line-clamp-2">{bm.description}</p>
                  <p className="text-gray-600 text-xs mt-1.5">
                    ~{bm.estimated_runtime_minutes}min · {bm.dataset_size} samples
                  </p>
                </button>
              );
            })}
          </div>
        )}
      </section>

      {/* Step 3: Subset */}
      <section>
        <h2 className="text-base font-semibold text-gray-200 mb-3">
          3. Dataset Size
        </h2>
        <div className="flex gap-2">
          {SUBSET_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setSubset(opt.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
                subset === opt.value
                  ? "bg-gray-700 border-gray-500 text-white"
                  : "bg-gray-900 border-gray-800 text-gray-400 hover:text-white hover:border-gray-600"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </section>

      {error && (
        <p className="text-red-400 text-sm bg-red-950 border border-red-800 rounded-lg px-4 py-3">
          {error}
        </p>
      )}

      {/* Run button */}
      <button
        onClick={handleRun}
        disabled={!selectedModel || selectedBenchmarks.size === 0 || submitting}
        className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
      >
        {submitting ? "Starting..." : "Run Evaluation"}
      </button>
    </div>
  );
}
