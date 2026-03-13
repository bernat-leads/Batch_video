const PIPELINE_STAGES = [
  "queued",
  "tts",
  "segmentation",
  "image_generation",
  "assembly",
  "completed",
] as const;

const STAGE_LABELS: Record<string, string> = {
  queued: "Queued",
  tts: "Audio",
  segmentation: "Segments",
  image_generation: "Images",
  assembly: "Assembly",
  completed: "Done",
};

interface StageIndicatorProps {
  currentStage: string;
  status: string;
}

export function StageIndicator({ currentStage, status }: StageIndicatorProps) {
  const currentIndex = PIPELINE_STAGES.indexOf(
    currentStage as (typeof PIPELINE_STAGES)[number],
  );

  return (
    <div className="flex items-center gap-1">
      {PIPELINE_STAGES.map((stage, index) => {
        const isPast = index < currentIndex;
        const isCurrent = index === currentIndex;
        const isCompleted = status === "completed";
        const isFailed = status === "failed";

        let bgColor = "var(--border-color)";
        if (isCompleted || isPast) bgColor = "var(--color-success)";
        else if (isCurrent && isFailed) bgColor = "var(--color-error)";
        else if (isCurrent) bgColor = "var(--brand)";

        return (
          <div
            key={stage}
            className="h-1.5 w-8 rounded-full transition-colors"
            style={{ backgroundColor: bgColor }}
            title={STAGE_LABELS[stage]}
          />
        );
      })}
    </div>
  );
}
