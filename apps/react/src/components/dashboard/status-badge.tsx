import { cn } from "@packages/ui/lib/utils";

const STATUS_CONFIG: Record<
  string,
  { label: string; bg: string; text: string; dot: string }
> = {
  pending: {
    label: "Pending",
    bg: "bg-status-info-light",
    text: "text-status-info",
    dot: "bg-status-info",
  },
  queued: {
    label: "Queued",
    bg: "bg-status-info-light",
    text: "text-status-info",
    dot: "bg-status-info",
  },
  processing: {
    label: "Processing",
    bg: "bg-status-warning-light",
    text: "text-brand",
    dot: "bg-brand",
  },
  tts: {
    label: "Generating Audio",
    bg: "bg-status-warning-light",
    text: "text-brand",
    dot: "bg-brand",
  },
  segmentation: {
    label: "Segmenting",
    bg: "bg-status-warning-light",
    text: "text-brand",
    dot: "bg-brand",
  },
  image_generation: {
    label: "Generating Images",
    bg: "bg-status-warning-light",
    text: "text-brand",
    dot: "bg-brand",
  },
  assembly: {
    label: "Assembling Video",
    bg: "bg-status-warning-light",
    text: "text-brand",
    dot: "bg-brand",
  },
  completed: {
    label: "Completed",
    bg: "bg-status-success-light",
    text: "text-status-success",
    dot: "bg-status-success",
  },
  failed: {
    label: "Failed",
    bg: "bg-status-error-light",
    text: "text-status-error",
    dot: "bg-status-error",
  },
};

interface StatusBadgeProps {
  status: string;
  stage?: string;
  className?: string;
}

export function StatusBadge({ status, stage, className }: StatusBadgeProps) {
  const key = status === "processing" && stage ? stage : status;
  const defaultConfig = { label: "Pending", bg: "bg-status-info-light", text: "text-status-info", dot: "bg-status-info" };
  const config = STATUS_CONFIG[key] ?? defaultConfig;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        config.bg,
        config.text,
        className,
      )}
    >
      <span
        className={cn("h-1.5 w-1.5 rounded-full", config.dot, {
          "animate-pulse": status === "processing",
        })}
      />
      {config.label}
    </span>
  );
}
