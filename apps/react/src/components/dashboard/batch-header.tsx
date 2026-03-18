import type { BatchRead } from "@packages/api-client";
import { cn } from "@packages/ui/lib/utils";
import { StatRow } from "@/components/ui/stat-row";
import { formatDuration, formatCurrency } from "@/lib/format";
import { CompletionChart } from "./completion-chart";

interface BatchStatsProps {
  batch: BatchRead;
}

/** Batch detail stats panel with completion chart, totals, and per-video averages. */
export function BatchStats({ batch }: BatchStatsProps) {
  const total = batch.total_videos;
  const completed = batch.completed_count ?? 0;
  const failed = batch.failed_count ?? 0;

  const totalTime = batch.duration_ms ?? 0;
  const totalCost = batch.total_cost_usd ?? 0;
  return (
    <div className="flex flex-wrap gap-4">
      <div className="min-w-[420px] flex-[3] flex flex-col gap-2">
        <p className="text-sm font-medium text-text-primary">Total</p>
        <div className="flex-1 rounded-xl border border-border bg-card-bg p-5">
          <div className="flex items-center gap-5">
            <div className="flex flex-1 items-center justify-center">
              <CompletionChart
                completed={completed}
                total={total}
                hasFailed={failed > 0 && completed + failed === total}
              />
            </div>
            <div className="w-px self-stretch bg-border" />
            <div className="flex-1 space-y-2 text-sm">
              <StatRow label="Total Videos" value={String(total)} />
              <StatRow label="Generated" value={String(completed)} />
              <StatRow
                label="Failed"
                value={String(failed)}
                valueClassName={cn(failed > 0 && "text-status-error")}
              />
            </div>
            <div className="w-px self-stretch bg-border" />
            <div className="flex-1 space-y-2 text-sm">
              <StatRow label="Video Length" value={formatDuration(totalTime)} />
              <StatRow label="Cost" value={formatCurrency(totalCost)} />
            </div>
          </div>
        </div>
      </div>
      <div className="min-w-[240px] flex-[2] flex flex-col gap-2">
        <p className="text-sm font-medium text-text-primary">Average per Video</p>
        <div className="flex-1 flex items-center rounded-xl border border-border bg-card-bg p-4">
          <div className="w-full space-y-2 text-sm">
            <StatRow
              label="Video Length"
              value={formatDuration(Math.round(totalTime / total))}
            />
            <StatRow
              label="Cost"
              value={formatCurrency(totalCost / total)}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
