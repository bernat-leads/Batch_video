interface PageHeaderProps {
  title: string;
  description: string;
}

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <div className="mb-6">
      <h1
        className="text-2xl font-semibold tracking-tight"
        style={{ color: "var(--text-primary)" }}
      >
        {title}
      </h1>
      <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
        {description}
      </p>
    </div>
  );
}
