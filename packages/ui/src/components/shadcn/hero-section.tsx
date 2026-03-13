import type { ReactNode } from "react";
import type { VariantProps } from "class-variance-authority";
import type { buttonVariants } from "@packages/ui/components/shadcn/button";
import { Button } from "@packages/ui/components/shadcn/button";
import { cn } from "@packages/ui/lib/utils";

interface HeroButtonProps {
  href: string;
  text: string;
  variant?: VariantProps<typeof buttonVariants>["variant"];
  icon?: ReactNode;
  iconRight?: ReactNode;
}

interface HeroSectionProps {
  title: string;
  subtitle?: string;
  description: string;
  badge?: ReactNode | false;
  buttons?: HeroButtonProps[] | false;
  visual?: ReactNode | false;
  className?: string;
  variant?: "default" | "centered" | "split" | "minimal";
}

export function HeroSection({
  title,
  subtitle,
  description,
  badge = false,
  buttons = false,
  visual = false,
  className,
  variant = "default",
}: HeroSectionProps) {
  const getVariantClasses = () => {
    switch (variant) {
      case "centered":
        return "text-center items-center";
      case "split":
        return "lg:grid-cols-2 lg:gap-12 lg:items-center";
      case "minimal":
        return "text-center items-center max-w-4xl mx-auto";
      default:
        return "text-center items-center";
    }
  };

  return (
    <section className={cn("overflow-hidden py-20 lg:py-32", className)}>
      <div className="mx-auto max-w-7xl px-6">
        <div className={cn("flex flex-col gap-12", getVariantClasses())}>
          {/* Content */}
          <div className="flex flex-col gap-8">
            {badge !== false && <div className="flex justify-center">{badge}</div>}

            <div className="space-y-6">
              {subtitle && (
                <p className="text-lg font-medium text-blue-600 dark:text-blue-400">{subtitle}</p>
              )}

              <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl lg:text-7xl dark:text-gray-100">
                {title}
              </h1>

              <p className="mx-auto max-w-3xl text-xl leading-relaxed text-gray-600 dark:text-gray-400">
                {description}
              </p>
            </div>

            {buttons !== false && buttons.length > 0 && (
              <div className="flex flex-col justify-center gap-4 sm:flex-row">
                {buttons.map((button, index) => (
                  <Button
                    key={index}
                    variant={button.variant ?? "default"}
                    size="lg"
                    asChild
                    className="min-w-[160px]"
                  >
                    <a href={button.href}>
                      {button.icon}
                      {button.text}
                      {button.iconRight}
                    </a>
                  </Button>
                ))}
              </div>
            )}
          </div>

          {/* Visual */}
          {visual !== false && variant === "split" && <div className="relative">{visual}</div>}

          {visual !== false && variant !== "split" && (
            <div className="relative mt-12">{visual}</div>
          )}
        </div>
      </div>
    </section>
  );
}
