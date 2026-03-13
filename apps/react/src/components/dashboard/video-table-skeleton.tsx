import { Skeleton } from "@packages/ui/components/shadcn/skeleton";

export function VideoTableSkeleton() {
  return (
    <div
      className="overflow-hidden rounded-xl border border-border bg-card-bg"
    >
      <div className="space-y-4 p-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton
              className="h-4 w-48 bg-border"
            />
            <Skeleton
              className="h-6 w-24 rounded-full bg-border"
            />
            <Skeleton
              className="h-2 w-32 bg-border"
            />
            <Skeleton
              className="h-12 w-9 rounded-md bg-border"
            />
            <Skeleton
              className="ml-auto h-8 w-20 rounded-lg bg-border"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
