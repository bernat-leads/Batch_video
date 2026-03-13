import type { DashboardStats } from "@packages/api-client";
import { SectionCard } from "@/components/ui/section-card";
import { StatRow } from "@/components/ui/stat-row";
import { formatCurrency, formatDuration } from "@/lib/format";

interface StatsCardsProps {
  stats: DashboardStats;
}

export function StatsCards({ stats }: StatsCardsProps) {
  return (
    <div className="flex flex-wrap gap-4">
      <SectionCard title="Total" className="min-w-[320px] flex-[3]">
        <div className="flex items-center gap-5">
          <div className="flex-1 space-y-2 text-sm">
            <StatRow label="Total Videos" value={stats.total_videos} />
            <StatRow label="Generated" value={stats.completed_videos} />
            <StatRow
              label="Failed"
              value={stats.failed_videos}
              valueClassName={
                stats.failed_videos > 0 ? "text-error" : undefined
              }
            />
          </div>
          <div className="self-stretch w-px bg-border" />
          <div className="flex-1 space-y-2 text-sm">
            <StatRow
              label="Tokens"
              value={stats.total_tokens.toLocaleString()}
            />
            <StatRow
              label="Video Length"
              value={formatDuration(stats.total_generation_time_ms)}
            />
            <StatRow
              label="Cost"
              value={formatCurrency(stats.total_cost_usd)}
            />
          </div>
        </div>
      </SectionCard>
      <SectionCard title="Average per Video" className="min-w-[240px] flex-[2]">
        <div className="space-y-2 text-sm">
          <StatRow
            label="Tokens"
            value={stats.avg_tokens_per_video.toLocaleString()}
          />
          <StatRow
            label="Video Length"
            value={formatDuration(stats.avg_generation_time_ms)}
          />
          <StatRow
            label="Cost"
            value={formatCurrency(stats.avg_cost_per_video_usd)}
          />
        </div>
      </SectionCard>
    </div>
  );
}
