import type { ReactNode } from "react";

import { cn } from "../../lib/utils";

interface GradientTextProps {
  children: ReactNode;
  className?: string;
  variant?: "primary" | "secondary" | "accent" | "custom";
  customGradient?: string;
}

export function GradientText({
  children,
  className,
  variant = "primary",
  customGradient,
}: GradientTextProps) {
  const getGradientClass = () => {
    switch (variant) {
      case "primary":
        return "bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-500 bg-clip-text text-transparent";
      case "secondary":
        return "bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 bg-clip-text text-transparent";
      case "accent":
        return "bg-gradient-to-r from-green-500 via-teal-500 to-blue-500 bg-clip-text text-transparent";
      case "custom":
        return (
          customGradient ??
          "bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent"
        );
      default:
        return "bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-500 bg-clip-text text-transparent";
    }
  };

  return <span className={cn(getGradientClass(), className)}>{children}</span>;
}
