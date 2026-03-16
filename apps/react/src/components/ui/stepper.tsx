import { Check } from "lucide-react";
import { cn } from "@packages/ui/lib/utils";

interface StepDef {
  key: string;
  label: string;
}

interface StepperProps {
  steps: StepDef[];
  current: string;
}

/** Horizontal multi-step indicator with completed/active/upcoming states. */
export function Stepper({ steps, current }: StepperProps) {
  const currentIdx = steps.findIndex((s) => s.key === current);

  return (
    <div className="flex w-full items-start">
      {steps.map((s, i) => {
        const isCompleted = i < currentIdx;
        const isCurrent = i === currentIdx;
        const isActive = isCompleted || isCurrent;

        return (
          <div key={s.key} className="flex flex-1 flex-col items-center gap-1.5">
            <div className="flex w-full items-center">
              {i > 0 && (
                <div
                  className={cn("h-px flex-1", isActive ? "bg-brand" : "bg-border")}
                />
              )}
              {i === 0 && <div className="flex-1" />}
              <div
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-medium",
                  isCompleted && "bg-brand text-white",
                  isCurrent &&
                    "border-[1.5px] border-brand bg-transparent text-brand",
                  !isCompleted &&
                    !isCurrent &&
                    "border-[1.5px] border-border bg-transparent text-text-muted",
                )}
              >
                {isCompleted ? <Check size={12} /> : i + 1}
              </div>
              {i < steps.length - 1 && (
                <div
                  className={cn(
                    "h-px flex-1",
                    isCompleted ? "bg-brand" : "bg-border",
                  )}
                />
              )}
              {i === steps.length - 1 && <div className="flex-1" />}
            </div>
            <span
              className={cn(
                "text-xs font-medium",
                isCompleted && "text-text-primary",
                isCurrent && "text-brand",
                !isCompleted && !isCurrent && "text-text-muted",
              )}
            >
              {s.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
