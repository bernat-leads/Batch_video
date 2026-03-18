import { cn } from "@packages/ui/lib/utils";

interface StatRowProps {
  label: string;
  value: string | number;
  valueClassName?: string;
}

/** Horizontal label–value pair used in statistics and detail cards. */
export function StatRow({ label, value, valueClassName }: StatRowProps) {
  return (
    <div className="flex items-center justify-between">
      <p className="text-xs text-text-muted">{label}</p>
      <p className={cn("text-sm font-medium text-text-primary", valueClassName)}>
        {String(value)}
      </p>
    </div>
  );
}
