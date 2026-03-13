import { Skeleton } from "@packages/ui/components/shadcn/skeleton";

export function VideoTableSkeleton() {
  return (
    <div
      className="overflow-hidden rounded-xl border"
      style={{
        borderColor: "var(--border-color)",
        backgroundColor: "var(--card-bg)",
      }}
    >
      <div className="space-y-4 p-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton
              className="h-4 w-48"
              style={{ backgroundColor: "var(--border-color)" }}
            />
            <Skeleton
              className="h-6 w-24 rounded-full"
              style={{ backgroundColor: "var(--border-color)" }}
            />
            <Skeleton
              className="h-2 w-32"
              style={{ backgroundColor: "var(--border-color)" }}
            />
            <Skeleton
              className="h-12 w-9 rounded-md"
              style={{ backgroundColor: "var(--border-color)" }}
            />
            <Skeleton
              className="ml-auto h-8 w-20 rounded-lg"
              style={{ backgroundColor: "var(--border-color)" }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
