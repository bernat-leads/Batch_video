import { Link } from "@tanstack/react-router";

interface BatchCardProps {
  batchId: string;
  total: number;
  completed: number;
  failed: number;
  processing: number;
  pending: number;
  createdAt: string;
}

export function BatchCard({
  batchId,
  total,
  completed,
  failed,
  processing,
  createdAt,
}: BatchCardProps) {
  const progressPercent =
    total > 0 ? Math.round((completed / total) * 100) : 0;
  const isAllDone = completed + failed === total && total > 0;

  return (
    <Link
      to="/app/batches/$batchId"
      params={{ batchId }}
      className="block rounded-xl border p-5 transition-all hover:shadow-md"
      style={{
        borderColor: "var(--border-color)",
        backgroundColor: "var(--card-bg)",
      }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p
            className="font-mono text-sm"
            style={{ color: "var(--text-secondary)" }}
          >
            Batch {batchId.slice(0, 8)}
          </p>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            {new Date(createdAt).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        </div>
        <div className="text-right">
          <p
            className="text-lg font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            {completed}/{total}
          </p>
          <p
            className="text-xs"
            style={{
              color: isAllDone ? "var(--color-success)" : "var(--brand)",
            }}
          >
            {isAllDone
              ? failed > 0
                ? "Completed with errors"
                : "All done"
              : `${processing} processing`}
          </p>
        </div>
      </div>

      <div className="mt-3">
        <div
          className="h-1.5 w-full overflow-hidden rounded-full"
          style={{ backgroundColor: "var(--border-color)" }}
        >
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${progressPercent}%`,
              backgroundColor:
                failed > 0 && isAllDone
                  ? "var(--color-error)"
                  : "var(--color-success)",
            }}
          />
        </div>
      </div>
    </Link>
  );
}
