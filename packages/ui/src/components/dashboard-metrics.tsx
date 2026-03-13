import { cva } from "class-variance-authority";
import type { VariantProps } from "class-variance-authority";
import { TrendingDown, TrendingUp } from "lucide-react";

import { cn } from "../lib/utils";

const dashboardMetricsVariants = cva("grid gap-6", {
  variants: {
    layout: {
      default: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
      compact: "grid-cols-2 md:grid-cols-4",
      wide: "grid-cols-1 md:grid-cols-5",
    },
    size: {
      sm: "gap-4",
      md: "gap-6",
      lg: "gap-8",
    },
  },
  defaultVariants: {
    layout: "default",
    size: "md",
  },
});

export interface MetricItem {
  title: string;
  value: string;
  change?: {
    value: string;
    isPositive: boolean;
  };
  icon?: React.ReactNode;
  trend?: "up" | "down" | "neutral";
}

export interface DashboardMetricsProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof dashboardMetricsVariants> {
  metrics: MetricItem[];
}

export function DashboardMetrics({
  className,
  layout,
  size,
  metrics,
  ...props
}: DashboardMetricsProps) {
  return (
    <div className={cn(dashboardMetricsVariants({ layout, size, className }))} {...props}>
      {metrics.map((metric, index) => (
        <div key={index} className="bg-card/50 rounded-lg border p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-muted-foreground text-sm font-medium">{metric.title}</p>
              <p className="text-foreground text-2xl font-bold">{metric.value}</p>
              {metric.change && (
                <div className="flex items-center gap-1">
                  {metric.trend === "up" && <TrendingUp className="h-4 w-4 text-emerald-400" />}
                  {metric.trend === "down" && <TrendingDown className="h-4 w-4 text-red-400" />}
                  <span
                    className={cn(
                      "text-sm font-medium",
                      metric.trend === "up" && "text-emerald-400",
                      metric.trend === "down" && "text-red-400",
                      metric.trend === "neutral" && "text-muted-foreground"
                    )}
                  >
                    {metric.change.value}
                  </span>
                </div>
              )}
            </div>
            {metric.icon && (
              <div className="bg-muted text-muted-foreground rounded-lg p-2">{metric.icon}</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
