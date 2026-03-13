import type { ReactNode } from "react";

import { cn } from "../../lib/utils";

interface StatItem {
  value: string;
  label: string;
  description?: string;
  icon?: ReactNode;
  trend?: {
    value: string;
    isPositive: boolean;
  };
}

interface StatsGridProps {
  stats: StatItem[];
  className?: string;
  variant?: "default" | "cards" | "minimal";
  columns?: 2 | 3 | 4;
}

export function StatsGrid({ stats, className, variant = "default", columns = 4 }: StatsGridProps) {
  const getGridCols = () => {
    switch (columns) {
      case 2:
        return "grid-cols-1 md:grid-cols-2";
      case 3:
        return "grid-cols-1 md:grid-cols-3";
      case 4:
        return "grid-cols-1 md:grid-cols-2 lg:grid-cols-4";
      default:
        return "grid-cols-1 md:grid-cols-2 lg:grid-cols-4";
    }
  };

  const getVariantClasses = () => {
    switch (variant) {
      case "cards":
        return "bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow duration-300";
      case "minimal":
        return "text-center";
      default:
        return "text-center";
    }
  };

  return (
    <div className={cn("w-full", className)}>
      <div className={cn("grid gap-6", getGridCols())}>
        {stats.map((stat, index) => (
          <div key={index} className={getVariantClasses()}>
            {variant === "cards" && stat.icon && (
              <div className="mb-4 flex justify-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/20">
                  {stat.icon}
                </div>
              </div>
            )}

            <div className="mb-2">
              <div className="text-3xl font-bold text-gray-900 md:text-4xl dark:text-gray-100">
                {stat.value}
              </div>
            </div>

            <div className="mb-2">
              <div className="text-lg font-semibold text-gray-700 dark:text-gray-300">
                {stat.label}
              </div>
            </div>

            {stat.description && (
              <div className="text-sm text-gray-600 dark:text-gray-400">{stat.description}</div>
            )}

            {stat.trend && (
              <div className="mt-3 flex items-center justify-center gap-1 text-sm">
                <span
                  className={cn(
                    "flex items-center gap-1",
                    stat.trend.isPositive
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  )}
                >
                  {stat.trend.isPositive ? (
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                  {stat.trend.value}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
