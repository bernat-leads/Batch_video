import { cva } from "class-variance-authority";
import type { VariantProps } from "class-variance-authority";

import { cn } from "../lib/utils";

const securityBadgeVariants = cva(
  "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "border border-slate-700 bg-slate-800 text-slate-300",
        success: "border border-emerald-800/30 bg-emerald-900/20 text-emerald-400",
        warning: "border border-amber-800/30 bg-amber-900/20 text-amber-400",
        danger: "border border-red-800/30 bg-red-900/20 text-red-400",
        info: "border border-blue-800/30 bg-blue-900/20 text-blue-400",
        new: "border border-orange-600 bg-orange-700 text-white",
      },
      size: {
        sm: "px-2 py-0.5 text-xs",
        md: "px-3 py-1 text-sm",
        lg: "px-4 py-1.5 text-base",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

export interface SecurityBadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof securityBadgeVariants> {
  children: React.ReactNode;
}

export function SecurityBadge({
  className,
  variant,
  size,
  children,
  ...props
}: SecurityBadgeProps) {
  return (
    <div className={cn(securityBadgeVariants({ variant, size, className }))} {...props}>
      {children}
    </div>
  );
}
