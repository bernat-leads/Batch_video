import type { VideoRead } from "@packages/api-client";

interface BatchHeaderProps {
  batchId: string;
  videos: VideoRead[];
}

export function BatchHeader({ batchId, videos }: BatchHeaderProps) {
  const total = videos.length;
  const completed = videos.filter((v) => v.status === "completed").length;
  const failed = videos.filter((v) => v.status === "failed").length;
  const processing = videos.filter((v) => v.status === "processing").length;
  const progressPercent =
    total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <div
      className="rounded-xl border p-6"
      style={{
        backgroundColor: "var(--card-bg)",
        borderColor: "var(--border-color)",
      }}
    >
      <div className="flex items-start justify-between">
        <div>
          <h1
            className="text-2xl font-semibold tracking-tight"
            style={{ color: "var(--text-primary)" }}
          >
            Batch Progress
          </h1>
          <p
            className="mt-1 font-mono text-sm"
            style={{ color: "var(--text-muted)" }}
          >
            {batchId.slice(0, 8)}...
          </p>
        </div>
        <div className="text-right">
          <p
            className="text-3xl font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            {completed}/{total}
          </p>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            videos complete
          </p>
        </div>
      </div>

      <div className="mt-4">
        <div
          className="h-2 w-full overflow-hidden rounded-full"
          style={{ backgroundColor: "var(--border-color)" }}
        >
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${progressPercent}%`,
              backgroundColor:
                failed > 0 && completed + failed === total
                  ? "var(--color-error)"
                  : "var(--color-success)",
            }}
          />
        </div>
      </div>

      <div className="mt-4 flex gap-6 text-sm">
        <span style={{ color: "var(--color-success)" }}>
          {completed} completed
        </span>
        {processing > 0 && (
          <span style={{ color: "var(--brand)" }}>
            {processing} processing
          </span>
        )}
        {failed > 0 && (
          <span style={{ color: "var(--color-error)" }}>{failed} failed</span>
        )}
        {total - completed - failed - processing > 0 && (
          <span style={{ color: "var(--color-info)" }}>
            {total - completed - failed - processing} queued
          </span>
        )}
      </div>
    </div>
  );
}
