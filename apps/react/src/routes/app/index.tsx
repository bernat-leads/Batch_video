import { createFileRoute } from "@tanstack/react-router";
import { useListBatchesApiV1VideosBatchesGet } from "@packages/api-client";
import { BatchCard } from "@/components/dashboard/batch-card";
import { EmptyState } from "@/components/dashboard/empty-state";
import { PageHeader } from "@/components/layout/page-header";
import { Skeleton } from "@packages/ui/components/shadcn/skeleton";

export const Route = createFileRoute("/app/")({
  component: HomePage,
});

function HomePage() {
  const { data: batches, isLoading } =
    useListBatchesApiV1VideosBatchesGet({
      query: { refetchInterval: 3000 },
    });

  return (
    <div>
      <PageHeader
        title="Videos"
        description="Monitor your video batch progress"
      />

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton
              key={i}
              className="h-28 w-full rounded-xl"
              style={{ backgroundColor: "var(--border-color)" }}
            />
          ))}
        </div>
      ) : !batches || batches.length === 0 ? (
        <EmptyState
          title="No batches yet"
          description="Upload an Excel file to start generating videos"
        />
      ) : (
        <div className="space-y-3">
          {batches.map((batch) => (
            <BatchCard
              key={batch.batch_id}
              batchId={batch.batch_id}
              total={batch.total}
              completed={batch.completed}
              failed={batch.failed}
              processing={batch.processing}
              pending={batch.pending}
              createdAt={batch.created_at}
            />
          ))}
        </div>
      )}
    </div>
  );
}
