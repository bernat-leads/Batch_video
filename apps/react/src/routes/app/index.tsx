import { createFileRoute } from "@tanstack/react-router";
import {
  useGetDashboardStatsApiV1VideosStatsDashboardGet,
  useListBatchesApiV1BatchesGet,
  useListVideosApiV1VideosGet,
} from "@packages/api-client";
import { Skeleton } from "@packages/ui/components/shadcn/skeleton";
import { DailyChart } from "@/components/dashboard/daily-chart";
import { RecentBatchesTable } from "@/components/dashboard/recent-batches-table";
import { RecentVideosTable } from "@/components/dashboard/recent-videos-table";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { PageHeader } from "@/components/layout/page-header";

export const Route = createFileRoute("/app/")({
  component: DashboardPage,
});

function DashboardPage() {
  const { data: dashboard, isLoading: statsLoading } =
    useGetDashboardStatsApiV1VideosStatsDashboardGet();
  const { data: batchesResponse } = useListBatchesApiV1BatchesGet({ page_size: 5 });
  const { data: videosResponse } = useListVideosApiV1VideosGet({
    page_size: 5,
  });

  if (statsLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Dashboard"
          description="Overview of your video pipeline"
        />
        <Skeleton className="h-[300px] w-full rounded-xl bg-border" />
        <div className="flex gap-4">
          <Skeleton className="h-32 flex-1 rounded-xl bg-border" />
          <Skeleton className="h-32 flex-1 rounded-xl bg-border" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Overview of your video pipeline"
      />
      {dashboard?.daily && dashboard.daily.length > 0 && (
        <DailyChart data={dashboard.daily} />
      )}
      {dashboard?.stats && <StatsCards stats={dashboard.stats} />}
      <div className="grid gap-6 lg:grid-cols-2">
        <RecentBatchesTable batches={(batchesResponse?.items ?? []).slice(0, 5)} />
        <RecentVideosTable
          videos={(videosResponse?.items ?? []).slice(0, 5)}
        />
      </div>
    </div>
  );
}
