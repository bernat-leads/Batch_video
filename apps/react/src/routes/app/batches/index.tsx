import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import type { BatchRead } from "@packages/api-client";
import {
  useListBatchesApiV1BatchesGet,
  getListBatchesApiV1BatchesGetQueryKey,
} from "@packages/api-client";
import { Skeleton } from "@packages/ui/components/shadcn/skeleton";
import { BatchTable } from "@/components/dashboard/batch-table";
import { CreateBatchDialog } from "@/components/dashboard/create-batch-dialog";
import { EmptyState } from "@/components/dashboard/empty-state";
import { SelectionToolbar } from "@/components/dashboard/selection-toolbar";
import { PageHeader } from "@/components/layout/page-header";
import { useDeleteBatch } from "@/hooks/use-delete-batch";

export const Route = createFileRoute("/app/batches/")({
  component: BatchesPage,
});

function BatchesPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const queryClient = useQueryClient();
  const { data: batchesResponse, isLoading } = useListBatchesApiV1BatchesGet({
    page,
    page_size: pageSize,
  });
  const [selectedBatches, setSelectedBatches] = useState<BatchRead[]>([]);

  const deleteBatch = useDeleteBatch();

  const handleBatchCreated = () => {
    queryClient.invalidateQueries({ queryKey: getListBatchesApiV1BatchesGetQueryKey() });
  };

  const handleDeleteSelected = () => {
    for (const batch of selectedBatches) {
      deleteBatch.mutate({ batchId: batch.id });
    }
    setSelectedBatches([]);
  };

  const batches = batchesResponse?.items ?? [];
  const hasSelection = selectedBatches.length > 0;

  return (
    <div>
      <PageHeader
        title="Batches"
        description="Manage your video batch jobs"
      />

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton
              key={i}
              className="h-28 w-full rounded-xl bg-border"
            />
          ))}
        </div>
      ) : batches.length === 0 && page === 1 ? (
        <EmptyState
          title="No batches yet"
          description="Upload an Excel file to start generating videos"
          action={<CreateBatchDialog onBatchCreated={handleBatchCreated} />}
        />
      ) : (
        <BatchTable
          batches={batches}
          onSelectionChange={setSelectedBatches}
          onDelete={(batchId) => deleteBatch.mutate({ batchId })}
          onRename={(_id, _newName) => {
            // TODO: add batch update/rename endpoint
          }}
          pagination={{
            page,
            totalPages: batchesResponse?.total_pages ?? 1,
            total: batchesResponse?.total ?? 0,
            pageSize,
            onPageChange: setPage,
            onPageSizeChange: (size) => {
              setPageSize(size);
              setPage(1);
            },
          }}
          toolbar={
            hasSelection ? (
              <SelectionToolbar
                count={selectedBatches.length}
                onExport={() => {}}
                onDelete={handleDeleteSelected}
              />
            ) : (
              <CreateBatchDialog onBatchCreated={handleBatchCreated} />
            )
          }
        />
      )}
    </div>
  );
}
