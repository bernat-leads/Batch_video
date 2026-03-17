import { createFileRoute } from "@tanstack/react-router";
import {
  useGetVideoApiV1VideosVideoIdGet,
  useGetBatchApiV1BatchesBatchIdGet,
  getGetVideoApiV1VideosVideoIdGetQueryKey,
} from "@packages/api-client";
import { videoEventsUrl } from "@packages/api-client/urls";
import { Skeleton } from "@packages/ui/components/shadcn/skeleton";
import { StageIndicator } from "@/components/dashboard/stage-indicator";
import { BreadcrumbNav } from "@/components/layout/breadcrumb-nav";
import { SectionCard } from "@/components/ui/section-card";
import { downloadVideo } from "@/lib/download";
import { useEventSource } from "@/hooks/use-event-source";
import { ShotsTable } from "./_components/shots-table";
import { VideoHeader } from "./_components/video-header";
import { VideoMetrics } from "./_components/video-metrics";
import { VideoPreview } from "./_components/video-preview";

export const Route = createFileRoute("/app/videos/$videoId")({
  component: VideoDetailPage,
});

/** Builds breadcrumb items based on whether the video belongs to a batch. */
function buildBreadcrumbs(videoId: string, batchId: string, batchName: string | null) {
  if (batchId && batchName) {
    return [
      { label: "Batches", to: "/app/batches" },
      { label: batchName, to: "/app/batches/$batchId", params: { batchId } },
      { label: `Video ${videoId.slice(0, 8)}` },
    ];
  }
  return [
    { label: "Videos", to: "/app/videos" },
    { label: `Video ${videoId.slice(0, 8)}` },
  ];
}

function VideoDetailPage() {
  const { videoId } = Route.useParams();

  const { data: video, isLoading } = useGetVideoApiV1VideosVideoIdGet(videoId);
  const batchId = video?.batch_id ?? "";
  const { data: batch } = useGetBatchApiV1BatchesBatchIdGet(batchId, {
    query: { enabled: !!batchId },
  });

  // Poll for updates while video is processing
  const isActive = video?.status === "processing";
  useEventSource(videoEventsUrl(videoId), !!isActive, [
    getGetVideoApiV1VideosVideoIdGetQueryKey(videoId),
  ]);

  if (isLoading) return <VideoDetailSkeleton />;

  if (!video) {
    return (
      <div className="space-y-6">
        <p className="text-text-muted">Video not found.</p>
      </div>
    );
  }

  const batchName = batch?.name ?? (batchId ? `Batch ${batchId.slice(0, 8)}` : null);
  const shots = video.shots ?? [];

  return (
    <div className="space-y-6">
      <BreadcrumbNav items={buildBreadcrumbs(videoId, batchId, batchName)} />

      <VideoHeader
        videoId={videoId}
        video={video}
        onDownload={() => downloadVideo(videoId)}
      />

      {video.error_message && (
        <div className="-mt-3 rounded-lg bg-status-error-light px-4 py-2">
          <p className="text-sm text-status-error">{video.error_message}</p>
        </div>
      )}

      {/* Hero: Preview + Info */}
      <div className="flex min-w-0 gap-6">
        <div className="w-[280px] shrink-0">
          <VideoPreview
            videoId={videoId}
            isFinished={video.status === "finished"}
            hasOutput={!!video.output_url}
          />
        </div>
        <VideoMetrics video={video} shots={shots} />
      </div>

      {/* Pipeline */}
      <div>
        <div className="mb-2">
          <p className="text-sm font-medium text-text-primary">Current Stage</p>
          <p className="text-xs text-text-muted">
            Audio, segmentation, image generation, and assembly stages
          </p>
        </div>
        <SectionCard>
          <StageIndicator
            currentStage={video.current_stage}
            status={video.status}
            variant="full"
          />
        </SectionCard>
      </div>

      <ShotsTable shots={shots} />
    </div>
  );
}

/** Loading skeleton matching the video detail page layout. */
function VideoDetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-6 w-64 bg-border" />
      <Skeleton className="h-16 w-full bg-border" />
      <div className="flex gap-6">
        <Skeleton className="h-[500px] w-[280px] rounded-xl bg-border" />
        <div className="flex min-w-[320px] flex-1 flex-col gap-5">
          <Skeleton className="h-[280px] rounded-xl bg-border" />
          <Skeleton className="h-[140px] rounded-xl bg-border" />
        </div>
      </div>
      <Skeleton className="h-[60px] w-full rounded-xl bg-border" />
    </div>
  );
}
