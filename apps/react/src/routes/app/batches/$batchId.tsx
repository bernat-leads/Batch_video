import { useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Download, Trash2 } from "lucide-react";
import type { VideoRead } from "@packages/api-client";
import {
  useGetBatchApiV1BatchesBatchIdGet,
  useListVideosApiV1VideosGet,
} from "@packages/api-client";
import { Button } from "@packages/ui/components/shadcn/button";
import { Skeleton } from "@packages/ui/components/shadcn/skeleton";
import { BatchStats } from "@/components/dashboard/batch-header";
import { SelectionToolbar } from "@/components/dashboard/selection-toolbar";
import { VideoTable } from "@/components/dashboard/video-table";
import { VideoTableSkeleton } from "@/components/dashboard/video-table-skeleton";
import { BreadcrumbNav } from "@/components/layout/breadcrumb-nav";
import { PageHeader } from "@/components/layout/page-header";
import { ConfirmDeleteDialog } from "@/components/ui/confirm-delete-dialog";
import { useDeleteBatch } from "@/hooks/use-delete-batch";
import { useDeleteVideo } from "@/hooks/use-delete-video";

export const Route = createFileRoute("/app/batches/$batchId")({
  component: BatchDetailPage,
});

function BatchDetailPage() {
  const { batchId } = Route.useParams();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const { data: batch, isLoading: batchLoading } = useGetBatchApiV1BatchesBatchIdGet(batchId);
  const { data: videosResponse, isLoading: videosLoading } = useListVideosApiV1VideosGet({
    batch_id: batchId,
    page,
    page_size: pageSize,
  });
  const [selectedVideos, setSelectedVideos] = useState<VideoRead[]>([]);

  const deleteVideo = useDeleteVideo();
  const deleteBatch = useDeleteBatch({
    onSuccess: () => navigate({ to: "/app/batches" }),
  });

  const handleDeleteSelected = () => {
    for (const video of selectedVideos) {
      deleteVideo.mutate({ videoId: video.id });
    }
    setSelectedVideos([]);
  };

  const isLoading = batchLoading || videosLoading;
  const videos = videosResponse?.items ?? [];
  const batchName = batch?.name ?? `Batch ${batchId.slice(0, 8)}`;

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
        description={`${batch?.name ?? ""} — Created ${batch?.created_at ? new Date(batch.created_at).toLocaleDateString() : ""}`}
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              disabled
              className="border-border text-text-secondary"
            >
              <Download size={14} className="mr-1.5" />
              Export ZIP
            </Button>
            <ConfirmDeleteDialog
              title="Delete batch?"
              description="This batch and all its videos will be permanently deleted."
              onConfirm={() => deleteBatch.mutate({ batchId })}
            >
              <Button
                variant="outline"
                size="sm"
                className="border-border text-status-error"
              >
                <Trash2 size={14} className="mr-1.5" />
                Delete
              </Button>
            </ConfirmDeleteDialog>
          </>
        }
      />
      {isLoading ? (
        <>
          <Skeleton className="h-36 w-full rounded-xl bg-border" />
          <VideoTableSkeleton />
        </>
      ) : (
        <>
          {batch && <BatchStats batch={batch} />}
          <p className="text-sm font-medium text-text-primary">Videos</p>
          <VideoTable
            videos={videos}
            onSelectionChange={setSelectedVideos}
            onDelete={(videoId) => deleteVideo.mutate({ videoId })}
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
                  onExport={() => {}}
                  onDelete={handleDeleteSelected}
                />
              ) : undefined
            }
          />
        </>
      )}
    </div>
  );
}
