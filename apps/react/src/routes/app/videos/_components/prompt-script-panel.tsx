import { useState } from "react";
import { ChevronRight } from "lucide-react";
import { cn } from "@packages/ui/lib/utils";

interface PromptScriptPanelProps {
  prompt?: string | null;
  scriptText: string;
}

/** Collapsible side-by-side panel showing the generation prompt and script text. */
export function PromptScriptPanel({ prompt, scriptText }: PromptScriptPanelProps) {
  const [open, setOpen] = useState(false);

  if (!prompt && !scriptText) return null;

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-sm text-text-muted transition-colors hover:text-text-secondary"
      >
        <ChevronRight
          size={14}
          className={cn("transition-transform", open && "rotate-90")}
        />
        {open ? "Hide" : "Show"} Prompt & Script
      </button>
      {open && (
        <div className="mt-3 flex gap-4">
          {prompt && (
            <div className="flex-1 rounded-xl border border-border bg-card-bg p-4">
              <p className="mb-1 text-xs font-medium text-text-muted">Prompt</p>
              <p className="text-sm leading-relaxed text-text-secondary">{prompt}</p>
            </div>
          )}
          <div className="flex-1 rounded-xl border border-border bg-card-bg p-4">
            <p className="mb-1 text-xs font-medium text-text-muted">Script</p>
            <p className="text-sm leading-relaxed text-text-primary">{scriptText}</p>
          </div>
        </div>
      )}
    </div>
  );
}
