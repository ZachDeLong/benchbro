const colors: Record<string, string> = {
  completed: "bg-green-900 text-green-300",
  running: "bg-blue-900 text-blue-300 animate-pulse",
  partial: "bg-yellow-900 text-yellow-300",
  failed: "bg-red-900 text-red-300",
  cancelled: "bg-gray-700 text-gray-400",
  pending: "bg-gray-800 text-gray-400",
  queued: "bg-gray-800 text-gray-400",
};

export default function StatusBadge({ status }: { status: string }) {
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
