import type { DashboardStats } from "@packages/api-client";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@packages/ui/components/shadcn/table";
import { cn } from "@packages/ui/lib/utils";
import { formatCurrency, formatDuration } from "@/lib/format";

interface StatsCardsProps {
  stats: DashboardStats;
}

/** Dashboard stats panel — video counts + cost/length table. */
export function StatsCards({ stats }: StatsCardsProps) {
  const videoCount = stats.total_videos || 1;
  const totalCost = stats.total_cost_usd ?? 0;
  const totalDuration = stats.total_duration_ms;

  return (
    <div className="flex flex-wrap gap-4">
      {/* Video counts */}
      <div className="min-w-[200px] flex-1 flex flex-col gap-2">
        <p className="text-sm font-medium text-text-primary">Videos</p>
        <div className="flex-1 overflow-hidden rounded-xl border border-border bg-card-bg">
          <Table>
            <TableBody>
              <TableRow className="border-border">
                <TableCell className="text-sm text-text-secondary">Total</TableCell>
                <TableCell className="text-right text-sm tabular-nums text-text-primary">{stats.total_videos}</TableCell>
              </TableRow>
              <TableRow className="border-border">
                <TableCell className="text-sm text-text-secondary">Generated</TableCell>
                <TableCell className="text-right text-sm tabular-nums text-text-primary">{stats.completed_videos}</TableCell>
              </TableRow>
              <TableRow className="border-border">
                <TableCell className="text-sm text-text-secondary">Failed</TableCell>
                <TableCell className={cn("text-right text-sm tabular-nums", stats.failed_videos > 0 ? "text-status-error" : "text-text-primary")}>
                  {stats.failed_videos}
                </TableCell>
              </TableRow>
              <TableRow className="border-border">
                <TableCell className="text-sm text-text-secondary">Batches</TableCell>
                <TableCell className="text-right text-sm tabular-nums text-text-primary">{stats.total_batches}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
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
                  {formatDuration(totalDuration)}
                </TableCell>
                <TableCell className="text-right text-sm tabular-nums text-text-primary">
                  {formatDuration(Math.round(totalDuration / videoCount))}
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
