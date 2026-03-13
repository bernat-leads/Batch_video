// Import icons used in the composite glyph
import { Shield } from "lucide-react";
import { cn } from "@packages/ui/lib/utils";

export const Logo = ({ className, uniColor }: { className?: string; uniColor?: boolean }) => {
  return (
    <div className={cn("flex items-center space-x-1.5", className)}>
      <div className="border-border/50 bg-background flex size-10 items-center justify-center rounded-lg border">
        <Shield className={cn("size-5", uniColor ? "text-foreground" : "text-muted-foreground")} />
      </div>
      <span className="font-serif text-2xl tracking-tight italic">Launch Check</span>
    </div>
  );
};

export const LogoIcon = ({ className, uniColor }: { className?: string; uniColor?: boolean }) => {
  return (
    <div
      className={cn(
        "border-border/50 bg-background flex size-10 items-center justify-center rounded-lg border",
        className
      )}
    >
      <Shield className={cn("size-5", uniColor ? "text-foreground" : "text-muted-foreground")} />
    </div>
  );
};

export const LogoStroke = ({ className }: { className?: string }) => {
  return (
    <div className={cn("flex items-center space-x-2", className)}>
      <div className="border-accent/20 flex size-8 items-center justify-center rounded-lg border">
        <Shield className="text-accent size-5" />
      </div>
      <span className="text-xl font-bold tracking-tight">Launch Check</span>
    </div>
  );
};
