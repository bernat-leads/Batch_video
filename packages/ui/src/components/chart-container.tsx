import { cva } from "class-variance-authority";
import type { VariantProps } from "class-variance-authority";

import { cn } from "../lib/utils";

const chartContainerVariants = cva("bg-card/50 rounded-lg border p-6", {
  variants: {
    variant: {
      default: "border-border",
      elevated: "border-border/70 bg-card/80 shadow-lg",
    },
    size: {
      sm: "p-4",
      md: "p-6",
      lg: "p-8",
    },
  },
  defaultVariants: {
    variant: "default",
    size: "md",
  },
});

export interface ChartContainerProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof chartContainerVariants> {
  title: string;
  children?: React.ReactNode;
  placeholder?: boolean;
}

export function ChartContainer({
  className,
  variant,
  size,
  title,
  children,
  placeholder = false,
  ...props
}: ChartContainerProps) {
  return (
    <div className={cn(chartContainerVariants({ variant, size, className }))} {...props}>
      <div className="mb-4">
        <h3 className="text-foreground text-lg font-semibold">{title}</h3>
      </div>

      {placeholder ? (
        <div className="bg-muted/50 border-border/50 flex h-64 items-center justify-center rounded-lg border border-dashed">
          <div className="text-muted-foreground text-center">
            <div className="mb-2 text-4xl">📊</div>
            <p className="text-sm">Chart placeholder</p>
          </div>
        </div>
      ) : (
        children
      )}
    </div>
  );
}
