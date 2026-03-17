import type { AICost, ShotRead, VideoReadWithShots } from "@packages/api-client";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@packages/ui/components/shadcn/table";
import { SectionCard } from "@/components/ui/section-card";
import { StatRow } from "@/components/ui/stat-row";
import { formatDuration, formatFileSize } from "@/lib/format";

interface VideoMetricsProps {
  video: VideoReadWithShots;
  shots: ShotRead[];
}

function formatCostPrecise(usd?: number): string {
  if (usd == null || usd === 0) return "\u2014";
  return `$${usd.toFixed(4)}`;
}

function formatTokens(count?: number): string {
  if (count == null || count === 0) return "\u2014";
  return count.toLocaleString();
}

const PIPELINE_STEPS = [
  { label: "TTS", key: "tts" as const },
  { label: "Segmentation", key: "segmentation" as const },
  { label: "Image Generation", key: "image_generation" as const },
];

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

      {/* Cost / Token Breakdown */}
      <div>
        <p className="mb-2 text-sm font-medium text-text-primary">Pipeline Cost</p>
        <div className="overflow-hidden rounded-xl border border-border bg-card-bg">
          <Table>
            <TableHeader>
              <TableRow className="border-border bg-content-bg">
                <TableHead className="text-text-secondary">Step</TableHead>
                <TableHead className="text-right text-text-secondary">Tokens</TableHead>
                <TableHead className="text-right text-text-secondary">Cost</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {PIPELINE_STEPS.map(({ label, key }) => {
                const cost: AICost | undefined = video[key];
                return (
                  <TableRow key={key} className="border-border">
                    <TableCell className="text-sm text-text-primary">{label}</TableCell>
                    <TableCell className="text-right text-sm tabular-nums text-text-secondary">
                      {formatTokens(cost?.token_count)}
                    </TableCell>
                    <TableCell className="text-right text-sm tabular-nums text-text-secondary">
                      {formatCostPrecise(cost?.cost_usd)}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
            <TableFooter>
              <TableRow className="border-border">
                <TableCell className="text-sm font-medium text-text-primary">Total</TableCell>
                <TableCell className="text-right text-sm font-medium tabular-nums text-text-primary">
                  {formatTokens(video.total?.token_count)}
                </TableCell>
                <TableCell className="text-right text-sm font-medium tabular-nums text-text-primary">
                  {formatCostPrecise(video.total?.cost_usd)}
                </TableCell>
              </TableRow>
            </TableFooter>
          </Table>
          <div className="border-t border-border px-3 py-2.5">
            <div className="flex items-center justify-between text-sm">
              <span className="text-text-muted">Duration</span>
              <span className="tabular-nums text-text-primary">
                {video.duration_ms ? formatDuration(video.duration_ms) : "\u2014"}
              </span>
            </div>
            <div className="mt-1 flex items-center justify-between text-sm">
              <span className="text-text-muted">Shots</span>
              <span className="tabular-nums text-text-primary">{shots.length}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
