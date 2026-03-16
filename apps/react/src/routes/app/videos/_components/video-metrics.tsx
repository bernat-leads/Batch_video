import type { AICost, ShotRead, VideoReadWithShots } from "@packages/api-client";
import { SectionCard } from "@/components/ui/section-card";
import { StatRow } from "@/components/ui/stat-row";
import { formatDuration, formatCurrency, formatFileSize } from "@/lib/format";

interface VideoMetricsProps {
  video: VideoReadWithShots;
  shots: ShotRead[];
}

function costValue(ai?: AICost): string {
  return ai?.cost_usd ? formatCurrency(ai.cost_usd) : "\u2014";
}

function tokenValue(ai?: AICost): string {
  return ai?.token_count ? ai.token_count.toLocaleString() : "\u2014";
}

export function VideoMetrics({ video, shots }: VideoMetricsProps) {
  const width = video.width ?? 1080;
  const height = video.height ?? 1920;

  return (
    <div className="flex min-w-[320px] flex-1 flex-col gap-5">
      {/* Details */}
      <div>
        <p className="mb-2 text-sm font-medium text-text-primary">Details</p>
        <SectionCard>
          <div className="space-y-2 text-sm">
            <StatRow label="Style" value={video.style ?? "\u2014"} valueClassName="capitalize" />
            <StatRow label="Voice ID" value={video.voice_id ?? "\u2014"} valueClassName="break-all" />
            <StatRow label="Top Text" value={video.top_text ?? "\u2014"} />
          </div>
          <div className="my-4 h-px bg-border" />
          <div className="space-y-2 text-sm">
            <StatRow label="Dimensions" value={`${width} \u00d7 ${height}`} />
            <StatRow label="File Size" value={formatFileSize(video.file_size_bytes ?? 0)} />
          </div>
        </SectionCard>
      </div>

      {/* Statistics */}
      <div>
        <p className="mb-2 text-sm font-medium text-text-primary">Statistics</p>
        <SectionCard>
          <div className="space-y-2 text-sm">
            <StatRow
              label="Video Length"
              value={video.duration_ms ? formatDuration(video.duration_ms) : "\u2014"}
            />
            <StatRow label="Shots" value={shots.length.toString()} />
            <StatRow label="TTS" value={costValue(video.tts)} />
            <StatRow
              label="Segmentation"
              value={`${tokenValue(video.segmentation)} tokens \u00b7 ${costValue(video.segmentation)}`}
            />
            <StatRow label="Image Gen" value={costValue(video.image_generation)} />
            <StatRow label="Total Cost" value={costValue(video.total)} />
            <StatRow label="Total Tokens" value={tokenValue(video.total)} />
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
