import type { ReactNode } from "react";

import { cn } from "../../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./card";

interface FeatureCardProps {
  title: string;
  description: string;
  icon?: ReactNode;
  className?: string;
  variant?: "default" | "highlighted" | "minimal";
  href?: string;
  onClick?: () => void;
}

export function FeatureCard({
  title,
  description,
  icon,
  className,
  variant = "default",
  href,
  onClick,
}: FeatureCardProps) {
  const getVariantClasses = () => {
    switch (variant) {
      case "highlighted":
        return "border-blue-500/20 bg-gradient-to-br from-blue-50/50 to-purple-50/50 dark:from-blue-950/20 dark:to-purple-950/20 hover:border-blue-500/40 hover:shadow-lg hover:shadow-blue-500/10";
      case "minimal":
        return "border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950 hover:border-gray-300 dark:hover:border-gray-700";
      default:
        return "border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950 hover:border-gray-300 dark:hover:border-gray-700 hover:shadow-md";
    }
  };

  const CardWrapper = href ? "a" : "div";
  const cardProps = href ? { href } : {};

  return (
    <CardWrapper
      {...cardProps}
      className={cn(
        "group transition-all duration-300 ease-in-out",
        variant === "highlighted" && "transform hover:-translate-y-1",
        className
      )}
      onClick={onClick}
    >
      <Card className={cn("h-full transition-all duration-300", getVariantClasses())}>
        <CardHeader className="pb-4">
          {icon && (
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 transition-colors duration-300 group-hover:bg-blue-200 dark:bg-blue-900/20 dark:group-hover:bg-blue-900/40">
              {icon}
            </div>
          )}
          <CardTitle className="text-lg font-semibold text-gray-900 transition-colors duration-300 group-hover:text-blue-600 dark:text-gray-100 dark:group-hover:text-blue-400">
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <CardDescription className="leading-relaxed text-gray-600 dark:text-gray-400">
            {description}
          </CardDescription>
        </CardContent>
      </Card>
    </CardWrapper>
  );
}
