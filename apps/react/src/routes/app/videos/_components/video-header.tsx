import type { VideoReadWithShots } from "@packages/api-client";
import { Download } from "lucide-react";
import { Button } from "@packages/ui/components/shadcn/button";
import { StatusBadge } from "@/components/dashboard/status-badge";

interface VideoHeaderProps {
  videoId: string;
  video: VideoReadWithShots;
  scriptPreview: string;
  onDownload: () => void;
}

export function VideoHeader({ videoId, video, scriptPreview, onDownload }: VideoHeaderProps) {
  return (
    <div className="mb-6 flex items-start justify-between gap-4">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight text-text-primary">
            Video {videoId.slice(0, 8)}
          </h1>
          <StatusBadge
            status={video.status}
            stage={video.current_stage}
          />
        </div>
        <p className="mt-1 text-sm text-text-secondary">
          {scriptPreview} — Created {new Date(video.created_at).toLocaleDateString()}
        </p>
      </div>
      <div className="flex items-center gap-2 pt-1">
        <Button
          variant="outline"
          size="sm"
          disabled={video.status !== "finished" || !video.output_url}
          onClick={onDownload}
          className="border-border text-text-secondary"
        >
          <Download size={14} className="mr-1.5" />
          Export
        </Button>
      </div>
    </div>
  );
}
