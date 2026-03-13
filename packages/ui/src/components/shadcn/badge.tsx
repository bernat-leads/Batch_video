import React from "react";
import { cva } from "class-variance-authority";
import type { VariantProps } from "class-variance-authority";

import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "font-inter focus:ring-ring inline-flex items-center gap-2 rounded-full border text-xs leading-4 font-bold transition-colors focus:ring-2 focus:ring-offset-2 focus:outline-none",
  {
    variants: {
      variant: {
        default: "border-[rgba(9,9,11,0.2)] bg-transparent text-[#A1A1AA]",
        primary: "border-[rgba(250,250,250,0.2)] bg-transparent text-[#FAFAFA]",
        secondary: "border-[rgba(250,250,250,0.1)] bg-[rgba(250,250,250,0.05)] text-[#A1A1AA]",
      },
      size: {
        default: "px-[10px] py-0",
        sm: "px-2 py-0.5 text-xs",
        lg: "px-3 py-1 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, size, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant, size, className }))} {...props} />;
}

export { Badge, badgeVariants };
