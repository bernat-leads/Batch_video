import { useState } from "react";
import { ChevronRight } from "lucide-react";
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
import { cn } from "@packages/ui/lib/utils";
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

function CollapsibleText({ label, text }: { label: string; text: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between text-sm"
      >
        <span className="text-text-muted">{label}</span>
        <ChevronRight
          size={14}
          className={cn(
            "text-text-muted transition-transform",
            open && "rotate-90",
          )}
        />
      </button>
      {open && (
        <p className="mt-1.5 text-sm leading-relaxed text-text-secondary">
          {text}
        </p>
      )}
    </div>
  );
}

export function VideoMetrics({ video, shots }: VideoMetricsProps) {
  return (
    <div className="flex min-w-[320px] flex-1 flex-col gap-5">
      {/* Input Details */}
      <div>
        <p className="mb-2 text-sm font-medium text-text-primary">Input</p>
        <SectionCard>
          <div className="space-y-2 text-sm">
            <StatRow label="Style" value={video.style ?? "\u2014"} valueClassName="capitalize" />
            <StatRow label="Voice ID" value={video.voice_id ?? "\u2014"} valueClassName="break-all" />
            <StatRow label="Top Text" value={video.top_text ?? "\u2014"} />
          </div>
          {(video.prompt || video.script_text) && (
            <>
              <div className="my-3 h-px bg-border" />
              <div className="space-y-2">
                {video.prompt && (
                  <CollapsibleText label="Prompt" text={video.prompt} />
                )}
                <CollapsibleText label="Script" text={video.script_text} />
              </div>
            </>
          )}
        </SectionCard>
      </div>

      {/* Pipeline Cost + Technical Details */}
      <div className="flex flex-wrap items-stretch gap-5">
        <div className="flex min-w-[280px] flex-1 flex-col">
          <p className="mb-2 text-sm font-medium text-text-primary">Pipeline Cost</p>
          <div className="flex-1 overflow-hidden rounded-xl border border-border bg-card-bg">
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
          </div>
        </div>

        <div className="flex min-w-[180px] flex-1 flex-col">
          <p className="mb-2 text-sm font-medium text-text-primary">Technical</p>
          <SectionCard className="flex-1">
            <div className="space-y-2 text-sm">
              <StatRow
                label="Duration"
                value={video.duration_ms ? formatDuration(video.duration_ms) : "\u2014"}
                valueClassName="tabular-nums"
              />
              <StatRow label="Shots" value={String(shots.length)} valueClassName="tabular-nums" />
              <StatRow
                label="File Size"
                value={video.file_size_bytes ? formatFileSize(video.file_size_bytes) : "\u2014"}
                valueClassName="tabular-nums"
              />
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
