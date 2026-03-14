import {
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
} from "recharts";
import type { BatchRead } from "@packages/api-client";
import { cn } from "@packages/ui/lib/utils";
import { StatRow } from "@/components/ui/stat-row";
import { formatDuration, formatCurrency } from "@/lib/format";

interface BatchStatsProps {
  batch: BatchRead;
}

function CompletionChart({
  completed,
  total,
  hasFailed,
}: {
  completed: number;
  total: number;
  hasFailed: boolean;
}) {
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
  const fill = hasFailed ? "var(--color-error)" : "var(--color-success)";
  const data = [{ value: percent }];

  return (
    <div className="flex shrink-0 flex-col items-center gap-1">
      <div className="relative h-[72px] w-[72px]">
        <RadialBarChart
          width={72}
          height={72}
          cx={36}
          cy={36}
          innerRadius={27}
          outerRadius={33}
          barSize={6}
          data={data}
          startAngle={90}
          endAngle={-270}
        >
          <PolarAngleAxis
            type="number"
            domain={[0, 100]}
            angleAxisId={0}
            tick={false}
          />
          <RadialBar
            background={{ fill: "var(--border-color)" }}
            dataKey="value"
            cornerRadius={3}
            fill={fill}
          />
        </RadialBarChart>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-sm font-semibold text-text-primary">
            {completed}/{total}
          </span>
        </div>
      </div>
      <span className="text-xs text-text-muted">Videos Completed</span>
    </div>
  );
}

export function BatchStats({ batch }: BatchStatsProps) {
  const total = batch.total_videos;
  const completed = batch.completed_count ?? 0;
  const failed = batch.failed_count ?? 0;

  const totalTokens = batch.tokens_used ?? 0;
  const totalTime = batch.generation_time_ms ?? 0;
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
              <StatRow label="Tokens" value={totalTokens.toLocaleString()} />
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
              label="Tokens"
              value={total > 0 ? Math.round(totalTokens / total).toLocaleString() : "0"}
            />
            <StatRow
              label="Video Length"
              value={total > 0 ? formatDuration(Math.round(totalTime / total)) : "0s"}
            />
            <StatRow
              label="Cost"
              value={total > 0 ? formatCurrency(totalCost / total) : "$0.00"}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
