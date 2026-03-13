import { useEffect, useState } from "react";
import type { ComponentPropsWithoutRef, CSSProperties, FC } from "react";
import { cn } from "@packages/ui/lib/utils";

export interface AnimatedShinyTextProps extends ComponentPropsWithoutRef<"span"> {
  shimmerWidth?: number;
  delay?: number;
}

export const AnimatedShinyText: FC<AnimatedShinyTextProps> = ({
  children,
  className,
  shimmerWidth = 100,
  delay = 0,
  ...props
}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <span
      style={
        {
          "--shiny-width": `${shimmerWidth}px`,
        } as CSSProperties
      }
      className={cn(
        "mx-auto max-w-md text-neutral-600/70 dark:text-neutral-400/70",

        // Shine effect
        isVisible &&
          "animate-shiny-text [background-size:var(--shiny-width)_100%] bg-clip-text [background-position:0_0] bg-no-repeat [transition:background-position_1s_cubic-bezier(.6,.6,0,1)_infinite]",

        // Shine gradient
        isVisible &&
          "bg-gradient-to-r from-transparent via-black/80 via-50% to-transparent dark:via-white/80",

        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};
