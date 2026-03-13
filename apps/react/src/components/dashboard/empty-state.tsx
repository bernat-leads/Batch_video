interface EmptyStateProps {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-xl border border-dashed py-16"
      style={{
        borderColor: "var(--text-muted)",
        backgroundColor: "var(--card-bg)",
      }}
    >
      <div
        className="mb-4 flex h-12 w-12 items-center justify-center rounded-full"
        style={{ backgroundColor: "var(--content-bg)" }}
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          style={{ color: "var(--text-muted)" }}
        >
          <path d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      </div>
      <h3
        className="text-lg font-medium"
        style={{ color: "var(--text-primary)" }}
      >
        {title}
      </h3>
      <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
        {description}
      </p>
    </div>
  );
}
