import { cn } from "@packages/ui/lib/utils";

interface SectionCardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function SectionCard({ title, children, className }: SectionCardProps) {
  return (
    <div className={cn("rounded-xl border border-border bg-card-bg p-5", className)}>
      {title && (
        <p className="mb-4 text-sm font-medium text-text-primary">{title}</p>
      )}
      {children}
    </div>
  );
}
