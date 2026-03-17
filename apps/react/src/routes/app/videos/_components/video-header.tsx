import type { VideoReadWithShots } from "@packages/api-client";
import { Download } from "lucide-react";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { AsyncButton } from "@/components/ui/async-button";

interface VideoHeaderProps {
  videoId: string;
  video: VideoReadWithShots;
  onDownload: () => Promise<void> | void;
}

function formatCreatedDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function VideoHeader({ videoId, video, onDownload }: VideoHeaderProps) {
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
          Created {formatCreatedDate(video.created_at)}
        </p>
      </div>
      <div className="flex items-center gap-2 pt-1">
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
