import { createFileRoute } from "@tanstack/react-router";
import { useListVideosApiV1VideosGet } from "@packages/api-client";
import { BatchHeader } from "@/components/dashboard/batch-header";
import { VideoTable } from "@/components/dashboard/video-table";
import { VideoTableSkeleton } from "@/components/dashboard/video-table-skeleton";
import { EmptyState } from "@/components/dashboard/empty-state";
import { Skeleton } from "@packages/ui/components/shadcn/skeleton";

export const Route = createFileRoute("/app/batches/$batchId")({
  component: BatchDetailPage,
});

function BatchDetailPage() {
  const { batchId } = Route.useParams();

  const { data, isLoading } = useListVideosApiV1VideosGet(
    { batch_id: batchId, page_size: 100 },
    {
      query: {
        refetchInterval: 3000,
      },
    },
  );

  const videos = data?.items ?? [];

  return (
    <div className="space-y-6">
      {isLoading ? (
        <>
          <Skeleton
            className="h-36 w-full rounded-xl"
            style={{ backgroundColor: "var(--border-color)" }}
          />
          <VideoTableSkeleton />
        </>
      ) : videos.length === 0 ? (
        <EmptyState
          title="No videos found"
          description="This batch doesn't contain any videos"
        />
      ) : (
        <>
          <BatchHeader batchId={batchId} videos={videos} />
          <VideoTable videos={videos} />
        </>
      )}
    </div>
  );
}
