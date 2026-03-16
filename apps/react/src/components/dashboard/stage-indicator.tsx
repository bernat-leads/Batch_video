import { cn } from "@packages/ui/lib/utils";
import {
  CheckCircle2,
  Clapperboard,
  Clock,
  ImageIcon,
  Mic,
  SplitSquareVertical,
  Upload,
} from "lucide-react";

/** Ordered list of pipeline stages. Order matters — determines progress position. */
const PIPELINE_STAGES = [
  "queued",
  "tts",
  "segmentation",
  "image_generation",
  "assembly",
  "upload",
  "done",
] as const;

const STAGE_META: Record<
  string,
  { label: string; icon: React.ElementType }
> = {
  queued: { label: "Queued", icon: Clock },
  tts: { label: "Audio (TTS)", icon: Mic },
  segmentation: { label: "Segmentation", icon: SplitSquareVertical },
  image_generation: { label: "Image Gen", icon: ImageIcon },
  assembly: { label: "Assembly", icon: Clapperboard },
  upload: { label: "Upload", icon: Upload },
  done: { label: "Done", icon: CheckCircle2 },
};

interface StageIndicatorProps {
  currentStage: string;
  status: string;
  variant?: "compact" | "full";
}

/**
 * Visual pipeline progress indicator.
 * - "compact": colored progress bars for table rows
 * - "full": icon + label pills for detail pages
 */
export function StageIndicator({
  currentStage,
  status,
  variant = "compact",
}: StageIndicatorProps) {
  const currentIndex = PIPELINE_STAGES.indexOf(
    currentStage as (typeof PIPELINE_STAGES)[number],
  );

  if (variant === "compact") {
    return (
      <div className="flex items-center gap-1">
        {PIPELINE_STAGES.map((stage, index) => {
          const isPast = index < currentIndex;
          const isCurrent = index === currentIndex;
          const isCompleted = status === "finished";
          const isFailed = status === "failed";

          let bgClass = "bg-border";
          if (isCompleted || isPast) bgClass = "bg-status-success";
          else if (isCurrent && isFailed) bgClass = "bg-status-error";
          else if (isCurrent) bgClass = "bg-brand";

          return (
            <div
              key={stage}
              className={cn(
                "h-1.5 w-8 rounded-full transition-colors",
                bgClass,
              )}
              title={STAGE_META[stage]?.label}
              aria-label={STAGE_META[stage]?.label}
            />
          );
        })}
      </div>
    );
  }

  return (
    <div className="flex w-full items-center gap-0">
      {PIPELINE_STAGES.map((stage, index) => {
        const meta = STAGE_META[stage]!;
        const Icon = meta.icon;
        const isPast = index < currentIndex;
        const isCurrent = index === currentIndex;
        const isCompleted = status === "finished";
        const isFailed = status === "failed";

        const done = isCompleted || isPast;
        const active = isCurrent && !isCompleted;
        const failed = isCurrent && isFailed;

        return (
          <div key={stage} className="flex min-w-0 flex-1 items-center">
            {index > 0 && (
              <div
                className={cn(
                  "h-px w-full min-w-2 max-w-6 shrink",
                  done ? "bg-status-success" : "bg-border",
                )}
              />
            )}
            <div
              className={cn(
                "flex w-full items-center justify-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium transition-colors",
                done &&
                  "bg-status-success-light text-status-success",
                active &&
                  !failed &&
                  "bg-brand/10 text-brand",
                failed &&
                  "bg-status-error-light text-status-error",
                !done &&
                  !active &&
                  "text-text-muted",
              )}
            >
              <Icon size={13} className="shrink-0" />
              <span className="truncate">{meta.label}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
