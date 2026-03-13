import { cn } from "@packages/ui/lib/utils";

const STATUS_CONFIG: Record<
  string,
  { label: string; bg: string; text: string; dot: string }
> = {
  pending: {
    label: "Pending",
    bg: "var(--color-info-light)",
    text: "var(--color-info)",
    dot: "var(--color-info)",
  },
  queued: {
    label: "Queued",
    bg: "var(--color-info-light)",
    text: "var(--color-info)",
    dot: "var(--color-info)",
  },
  processing: {
    label: "Processing",
    bg: "var(--color-warning-light)",
    text: "var(--brand)",
    dot: "var(--brand)",
  },
  tts: {
    label: "Generating Audio",
    bg: "var(--color-warning-light)",
    text: "var(--brand)",
    dot: "var(--brand)",
  },
  segmentation: {
    label: "Segmenting",
    bg: "var(--color-warning-light)",
    text: "var(--brand)",
    dot: "var(--brand)",
  },
  image_generation: {
    label: "Generating Images",
    bg: "var(--color-warning-light)",
    text: "var(--brand)",
    dot: "var(--brand)",
  },
  assembly: {
    label: "Assembling Video",
    bg: "var(--color-warning-light)",
    text: "var(--brand)",
    dot: "var(--brand)",
  },
  completed: {
    label: "Completed",
    bg: "var(--color-success-light)",
    text: "var(--color-success)",
    dot: "var(--color-success)",
  },
  failed: {
    label: "Failed",
    bg: "var(--color-error-light)",
    text: "var(--color-error)",
    dot: "var(--color-error)",
  },
};

interface StatusBadgeProps {
  status: string;
  stage?: string;
  className?: string;
}

export function StatusBadge({ status, stage, className }: StatusBadgeProps) {
  const key = status === "processing" && stage ? stage : status;
  const defaultConfig = { label: "Pending", bg: "var(--color-info-light)", text: "var(--color-info)", dot: "var(--color-info)" };
  const config = STATUS_CONFIG[key] ?? defaultConfig;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        className,
      )}
      style={{ backgroundColor: config.bg, color: config.text }}
    >
      <span
        className={cn("h-1.5 w-1.5 rounded-full", {
          "animate-pulse": status === "processing",
        })}
        style={{ backgroundColor: config.dot }}
      />
      {config.label}
    </span>
  );
}
