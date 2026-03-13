import { Loader2 } from "lucide-react";
import { cn } from "@packages/ui/lib/utils";

interface LoadingProps {
  className?: string;
  text?: string;
}

export function Loading({ className, text = "Loading..." }: LoadingProps) {
  return (
    <div
      className={cn(
        "bg-background/80 fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm",
        className
      )}
    >
      <div className="flex flex-col items-center space-y-4">
        <Loader2 className="text-primary h-8 w-8 animate-spin" />
        <p className="text-muted-foreground text-sm">{text}</p>
      </div>
    </div>
  );
}

// Alternative loading component with skeleton
export function LoadingSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "bg-background/80 fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm",
        className
      )}
    >
      <div className="flex flex-col items-center space-y-4">
        <div className="border-primary h-8 w-8 animate-spin rounded-full border-4 border-t-transparent" />
        <div className="bg-muted h-4 w-24 animate-pulse rounded" />
      </div>
    </div>
  );
}

// Minimal loading spinner
export function LoadingSpinner({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "bg-background/80 fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm",
        className
      )}
    >
      <Loader2 className="text-primary h-8 w-8 animate-spin" />
    </div>
  );
}
