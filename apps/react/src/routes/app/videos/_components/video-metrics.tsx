import { useState } from "react";
import { ChevronRight } from "lucide-react";
import type { ShotRead, VideoReadWithShots } from "@packages/api-client";
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

function formatUsage(count: number | undefined, unit: string): string {
  if (count == null || count === 0) return "\u2014";
  return `${count.toLocaleString()} ${unit}`;
}

/** Map model name to the unit its token_count represents. */
function getUsageUnit(model: string): string {
  if (model.includes("eleven")) return "chars";
  if (model.includes("imagen")) return "images";
  return "tokens";
}

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
        <pre className="mt-1.5 whitespace-pre-wrap font-sans text-sm leading-relaxed text-text-secondary">
          {text}
        </pre>
      )}
    </div>
  );
}

export function VideoMetrics({ video, shots }: VideoMetricsProps) {
  const modelCosts = video.model_costs ?? {};
  const totalCostUsd = video.total_cost_usd ?? 0;

  return (
    <div className="flex min-w-[320px] flex-1 flex-col gap-5">
      {/* Input Details */}
      <div>
        <p className="mb-2 text-sm font-medium text-text-primary">Input</p>
        <SectionCard>
          <div className="space-y-2 text-sm">
            <StatRow label="Style" value={video.style ?? "\u2014"} valueClassName="capitalize" />
            <StatRow label="Voice ID" value={video.voice_id || "\u2014"} valueClassName="break-all" />
            <StatRow label="Top Text" value={video.top_text ?? "\u2014"} />
          </div>
          {/* eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing -- intentionally treat empty string as falsy */}
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
                  <TableHead className="text-text-secondary">Model</TableHead>
                  <TableHead className="text-right text-text-secondary">Usage</TableHead>
                  <TableHead className="text-right text-text-secondary">Cost</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(modelCosts).map(([model, cost]) => (
                  <TableRow key={model} className="border-border">
                    <TableCell className="font-mono text-xs text-text-primary">
                      {model}
                    </TableCell>
                    <TableCell className="text-right text-sm tabular-nums text-text-secondary">
                      {formatUsage(cost.token_count, getUsageUnit(model))}
                    </TableCell>
                    <TableCell className="text-right text-sm tabular-nums text-text-secondary">
                      {formatCostPrecise(cost.cost_usd)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
              <TableFooter>
                <TableRow className="border-border">
                  <TableCell colSpan={2} className="text-sm font-medium text-text-primary">Total</TableCell>
                  <TableCell className="text-right text-sm font-medium tabular-nums text-text-primary">
                    {formatCostPrecise(totalCostUsd)}
                  </TableCell>
                </TableRow>
              </TableFooter>
            </Table>
            {totalCostUsd > 0 && video.duration_ms ? (
              <div className="border-t border-border px-3 py-2 text-right text-xs text-text-muted">
                {formatCostPrecise(totalCostUsd / (video.duration_ms / 60000))}/min
              </div>
            ) : null}
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
