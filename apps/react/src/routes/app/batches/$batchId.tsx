import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { AlertCircle, Download, RotateCcw } from "lucide-react";
import type { VideoRead } from "@packages/api-client";
import {
  useGetBatchApiV1BatchesBatchIdGet,
  useListVideosApiV1VideosGet,
  useBulkRetryVideosApiV1VideosBulkRetryPost,
  getGetBatchApiV1BatchesBatchIdGetQueryKey,
  getListVideosApiV1VideosGetQueryKey,
} from "@packages/api-client";
import { Skeleton } from "@packages/ui/components/shadcn/skeleton";
import { AsyncButton } from "@/components/ui/async-button";
import { BatchStats } from "@/components/dashboard/batch-header";
import { SelectionToolbar } from "@/components/dashboard/selection-toolbar";
import { VideoTable } from "@/components/dashboard/video-table";
import { VideoTableSkeleton } from "@/components/dashboard/video-table-skeleton";
import { BreadcrumbNav } from "@/components/layout/breadcrumb-nav";
import { PageHeader } from "@/components/layout/page-header";
import { batchEventsUrl } from "@packages/api-client/urls";
import { exportBatchZip, exportSelectedVideosZip } from "@/lib/download";
import { useEventSource } from "@/hooks/use-event-source";

export const Route = createFileRoute("/app/batches/$batchId")({
  component: BatchDetailPage,
});

function BatchDetailPage() {
  const { batchId } = Route.useParams();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const { data: batch, isLoading: batchLoading } = useGetBatchApiV1BatchesBatchIdGet(batchId);
  const { data: videosResponse, isLoading: videosLoading } = useListVideosApiV1VideosGet({
    batch_id: batchId,
    page,
    page_size: pageSize,
  });
  const [selectedVideos, setSelectedVideos] = useState<VideoRead[]>([]);
  const { mutateAsync: bulkRetry } = useBulkRetryVideosApiV1VideosBulkRetryPost();

  const isActive = !!batch && batch.status === "processing";
  useEventSource(batchEventsUrl(batchId), isActive, [
    getGetBatchApiV1BatchesBatchIdGetQueryKey(batchId),
    getListVideosApiV1VideosGetQueryKey({ batch_id: batchId }),
  ]);

  const isLoading = batchLoading || videosLoading;
  const videos = videosResponse?.items ?? [];
  const batchName = batch?.name ?? `Batch ${batchId.slice(0, 8)}`;
  const failedVideos = videos.filter((v) => v.status === "failed");
  const selectedFailed = selectedVideos.filter((v) => v.status === "failed");

  const invalidateQueries = () => {
    void queryClient.invalidateQueries({ queryKey: getGetBatchApiV1BatchesBatchIdGetQueryKey(batchId) });
    void queryClient.invalidateQueries({ queryKey: getListVideosApiV1VideosGetQueryKey({ batch_id: batchId }) });
  };

  const handleBulkRetry = async (videoIds: string[]) => {
    if (!videoIds.length) return;
    await bulkRetry({ data: { video_ids: videoIds } });
    invalidateQueries();
  };

  return (
    <div className="space-y-6">
      <BreadcrumbNav
        items={[
          { label: "Batches", to: "/app/batches" },
          { label: batchName },
        ]}
      />
      <PageHeader
        title={batchName}
        description={batch?.created_at ? `Created ${new Date(batch.created_at).toLocaleDateString()}` : ""}
        actions={
          <div className="flex items-center gap-2">
            {failedVideos.length > 0 && (
              <AsyncButton
                onClick={() => handleBulkRetry(failedVideos.map((v) => v.id))}
                icon={<RotateCcw size={14} />}
                label={`Retry ${failedVideos.length} Failed`}
                loadingLabel="Retrying..."
              />
            )}
            <AsyncButton
              disabled={!batch || (batch.completed_count ?? 0) === 0}
              onClick={() => exportBatchZip(batchId, batch?.name ?? "batch")}
              icon={<Download size={14} />}
              label="Export Batch ZIP"
              loadingLabel="Exporting..."
            />
          </div>
        }
      />
      {isLoading ? (
        <>
          <Skeleton className="h-36 w-full rounded-xl bg-border" />
          <VideoTableSkeleton />
        </>
      ) : (
        <>
          {batch?.error_message && (
            <div className="flex items-start gap-3 rounded-xl border border-status-error/30 bg-status-error-light p-4">
              <AlertCircle size={18} className="mt-0.5 shrink-0 text-status-error" />
              <div>
                <p className="text-sm font-medium text-status-error">Processing failed</p>
                <p className="mt-1 text-sm text-text-secondary">{batch.error_message}</p>
              </div>
            </div>
          )}
          {batch && <BatchStats batch={batch} />}
          <p className="text-sm font-medium text-text-primary">Videos</p>
          <VideoTable
            videos={videos}
            onSelectionChange={setSelectedVideos}
            pagination={{
              page,
              totalPages: videosResponse?.total_pages ?? 1,
              total: videosResponse?.total ?? 0,
              pageSize,
              onPageChange: setPage,
              onPageSizeChange: (size) => {
                setPageSize(size);
                setPage(1);
              },
            }}
            toolbar={
              selectedVideos.length > 0 ? (
                <SelectionToolbar
                  count={selectedVideos.length}
                  exportLabel="Export Selected Videos"
                  onExport={() => exportSelectedVideosZip(selectedVideos.map((v) => v.id))}
                  onRetry={() => handleBulkRetry(selectedFailed.map((v) => v.id))}
                  retryCount={selectedFailed.length}
                />
              ) : undefined
            }
          />
        </>
      )}
    </div>
  );
}
