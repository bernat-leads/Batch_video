import type { BatchRead } from "@packages/api-client";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@packages/ui/components/shadcn/table";
import { cn } from "@packages/ui/lib/utils";
import { formatDuration, formatCurrency } from "@/lib/format";
import { CompletionChart } from "./completion-chart";

interface BatchStatsProps {
  batch: BatchRead;
}

/** Batch detail stats panel — completion chart, video counts, cost & length table. */
export function BatchStats({ batch }: BatchStatsProps) {
  const total = batch.total_videos ?? 0;
  const completed = batch.completed_count ?? 0;
  const failed = batch.failed_count ?? 0;
  const videoCount = total || 1;

  const totalTime = batch.duration_ms ?? 0;
  const totalCost = batch.total_cost_usd ?? 0;

  return (
    <div className="flex flex-wrap gap-4">
      {/* Completion chart + video counts */}
      <div className="min-w-[320px] flex-[2] flex flex-col gap-2">
        <p className="text-sm font-medium text-text-primary">Videos</p>
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
            <div className="flex-1 overflow-hidden">
              <Table>
                <TableBody>
                  <TableRow className="border-border">
                    <TableCell className="text-sm text-text-secondary py-1.5 pl-0">Total</TableCell>
                    <TableCell className="text-right text-sm tabular-nums text-text-primary py-1.5 pr-0">{total}</TableCell>
                  </TableRow>
                  <TableRow className="border-border">
                    <TableCell className="text-sm text-text-secondary py-1.5 pl-0">Generated</TableCell>
                    <TableCell className="text-right text-sm tabular-nums text-text-primary py-1.5 pr-0">{completed}</TableCell>
                  </TableRow>
                  <TableRow className="border-border">
                    <TableCell className="text-sm text-text-secondary py-1.5 pl-0">Failed</TableCell>
                    <TableCell className={cn("text-right text-sm tabular-nums py-1.5 pr-0", failed > 0 ? "text-status-error" : "text-text-primary")}>
                      {failed}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </div>
        </div>
      </div>

      {/* Cost & length — total vs average */}
      <div className="min-w-[320px] flex-[2] flex flex-col gap-2">
        <p className="text-sm font-medium text-text-primary">Cost & Length</p>
        <div className="flex-1 overflow-hidden rounded-xl border border-border bg-card-bg">
          <Table>
            <TableHeader>
              <TableRow className="border-border bg-content-bg">
                <TableHead className="text-text-secondary" />
                <TableHead className="text-right text-text-secondary">Total</TableHead>
                <TableHead className="text-right text-text-secondary">Avg / Video</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow className="border-border">
                <TableCell className="text-sm text-text-secondary">Video Length</TableCell>
                <TableCell className="text-right text-sm tabular-nums text-text-primary">
                  {formatDuration(totalTime)}
                </TableCell>
                <TableCell className="text-right text-sm tabular-nums text-text-primary">
                  {formatDuration(Math.round(totalTime / videoCount))}
                </TableCell>
              </TableRow>
              <TableRow className="border-border">
                <TableCell className="text-sm text-text-secondary">Cost</TableCell>
                <TableCell className="text-right text-sm tabular-nums text-text-primary">
                  {formatCurrency(totalCost)}
                </TableCell>
                <TableCell className="text-right text-sm tabular-nums text-text-primary">
                  {formatCurrency(totalCost / videoCount)}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}
