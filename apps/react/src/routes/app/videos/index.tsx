import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import type { VideoRead } from "@packages/api-client";
import {
  useListVideosApiV1VideosGet,
  useListBatchesApiV1BatchesGet,
} from "@packages/api-client";

import { CreateVideoDialog } from "@/components/dashboard/create-video-dialog";
import { exportSelectedVideosZip } from "@/lib/download";
import { EmptyState } from "@/components/dashboard/empty-state";
import { SelectionToolbar } from "@/components/dashboard/selection-toolbar";
import { VideoTable } from "@/components/dashboard/video-table";
import { VideoTableSkeleton } from "@/components/dashboard/video-table-skeleton";
import { usePaginationState } from "@/hooks/use-pagination-state";
import { PageHeader } from "@/components/layout/page-header";

export const Route = createFileRoute("/app/videos/")({
  component: VideosPage,
});

function VideosPage() {
  const { page, pageSize, paginationProps: rawPagination } = usePaginationState(20);
  const { data: videosResponse, isLoading: videosLoading } = useListVideosApiV1VideosGet({
    page,
    page_size: pageSize,
  });
  const paginationProps = {
    ...rawPagination,
    totalPages: videosResponse?.total_pages ?? 1,
    total: videosResponse?.total ?? 0,
  };
  const { data: batchesResponse } = useListBatchesApiV1BatchesGet({ page_size: 1000 });
  const [selectedVideos, setSelectedVideos] = useState<VideoRead[]>([]);

  const videos = videosResponse?.items ?? [];

  const batchInfo = useMemo(() => {
    const batches = batchesResponse?.items;
    if (!batches) return undefined;
    const map: Record<string, { name: string }> = {};
    for (const b of batches) {
      map[b.id] = { name: b.name };
    }
    return map;
  }, [batchesResponse]);

  const hasSelection = selectedVideos.length > 0;

  return (
    <div>
      <PageHeader
        title="Videos"
        description="All videos across batches"
      />

      {videosLoading ? (
        <VideoTableSkeleton />
      ) : videos.length === 0 && page === 1 ? (
        <EmptyState
          title="No videos yet"
          description="Create a batch to start generating videos"
          action={<CreateVideoDialog />}
        />
      ) : (
        <VideoTable
          videos={videos}
          batches={batchInfo}
          showIndex={false}
          onSelectionChange={setSelectedVideos}
          pagination={paginationProps}
          toolbar={
            hasSelection ? (
              <SelectionToolbar
                count={selectedVideos.length}
                exportLabel="Export Selected Videos"
                onExport={() => exportSelectedVideosZip(selectedVideos.map((v) => v.id))}
              />
            ) : (
              <CreateVideoDialog />
            )
          }
        />
      )}
    </div>
  );
}
