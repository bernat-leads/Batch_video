import { cva } from "class-variance-authority";
import type { VariantProps } from "class-variance-authority";

import { cn } from "../lib/utils";

const securityFeatureCardVariants = cva(
  "group bg-card/50 relative overflow-hidden rounded-xl border p-8",
  {
    variants: {
      variant: {
        default: "border-border",
        featured: "border-orange-500/30 bg-gradient-to-br from-orange-500/5 to-transparent",
        success: "border-emerald-500/30 bg-gradient-to-br from-emerald-500/5 to-transparent",
        info: "border-blue-500/30 bg-gradient-to-br from-blue-500/5 to-transparent",
      },
      size: {
        sm: "p-6",
        md: "p-8",
        lg: "p-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

export interface SecurityFeatureCardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof securityFeatureCardVariants> {
  title: string;
  description: string;
  icon?: React.ReactNode;
  visual?: React.ReactNode;
  cta?: React.ReactNode;
}

export function SecurityFeatureCard({
  className,
  variant,
  size,
  title,
  description,
  icon,
  visual,
  cta,
  ...props
}: SecurityFeatureCardProps) {
  return (
    <div className={cn(securityFeatureCardVariants({ variant, size, className }))} {...props}>
      {/* Background glow effect */}
      <div className="via-muted/5 absolute inset-0 bg-gradient-to-br from-transparent to-transparent opacity-0"></div>

      <div className="relative z-10 space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <h3 className="text-foreground text-xl font-semibold">{title}</h3>
            <p className="text-muted-foreground leading-relaxed">{description}</p>
          </div>
          {icon && <div className="bg-muted text-muted-foreground rounded-lg p-3">{icon}</div>}
        </div>

        {/* Visual element */}
        {visual && (
          <div className="flex justify-center">
            <div className="relative">
              {visual}
              {/* Subtle glow effect */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent via-orange-500/10 to-transparent opacity-0 blur-xl"></div>
            </div>
          </div>
        )}

        {/* CTA */}
        {cta && <div className="pt-4">{cta}</div>}
      </div>
    </div>
  );
}
