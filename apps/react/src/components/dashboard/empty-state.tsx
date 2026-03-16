import { Video } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
}

/** Centered placeholder shown when a list has no items (e.g. no videos, no batches). */
export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-xl border border-dashed border-text-muted bg-card-bg py-16"
    >
      <div
        className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-content-bg"
      >
        <Video size={24} strokeWidth={1.5} className="text-text-muted" />
      </div>
      <h3
        className="text-lg font-medium text-text-primary"
      >
        {title}
      </h3>
      <p className="mt-1 text-sm text-text-muted">
        {description}
      </p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
