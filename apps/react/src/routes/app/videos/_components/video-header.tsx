import type { VideoReadWithShots } from "@packages/api-client";
import { Download, Film, RotateCcw } from "lucide-react";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { formatDate } from "@/lib/format";
import { AsyncButton } from "@/components/ui/async-button";

interface VideoHeaderProps {
  videoId: string;
  video: VideoReadWithShots;
  onDownload: () => Promise<void> | void;
  onRetry: () => Promise<void> | void;
  onRestartAssembly: () => Promise<void> | void;
}

export function VideoHeader({ videoId, video, onDownload, onRetry, onRestartAssembly }: VideoHeaderProps) {
  const canRestartAssembly =
    video.status === "finished" || video.status === "failed";

  return (
    <div className="mb-6 flex items-start justify-between gap-4">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight text-text-primary">
            Video {videoId.slice(0, 8)}
          </h1>
          <StatusBadge status={video.status} stage={video.current_stage} />
        </div>
        <p className="mt-0.5 text-xs text-text-muted">
          Created {formatDate(video.created_at)}
        </p>
      </div>
      <div className="flex items-center gap-2 pt-1">
        {video.status === "failed" && (
          <AsyncButton
            onClick={onRetry}
            icon={<RotateCcw size={14} />}
            label="Retry"
            loadingLabel="Retrying..."
          />
        )}
        {canRestartAssembly && (
          <AsyncButton
            onClick={onRestartAssembly}
            icon={<Film size={14} />}
            label="Re-render"
            loadingLabel="Re-rendering..."
          />
        )}
        <AsyncButton
          onClick={onDownload}
          icon={<Download size={14} />}
          label="Export"
          loadingLabel="Exporting..."
          disabled={video.status !== "finished" || !video.output_url}
        />
      </div>
    </div>
  );
}
