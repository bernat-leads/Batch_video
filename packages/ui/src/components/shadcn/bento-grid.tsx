import React from "react";

import { cn } from "../../lib/utils";
import { H2 } from "./typography";

interface BentoGridProps extends React.HTMLAttributes<HTMLElement> {
  title: string;
  children: React.ReactNode;
}

const BentoGrid = React.forwardRef<HTMLElement, BentoGridProps>(
  ({ className, title, children, ...props }, ref) => (
    <section
      ref={ref}
      className={cn(
        "mx-auto flex max-w-[1312px] flex-col items-start gap-12 bg-black px-8 py-20",
        className
      )}
      {...props}
    >
      <H2>{title}</H2>

      <div className="flex w-full flex-col items-start gap-4">{children}</div>
    </section>
  )
);
BentoGrid.displayName = "BentoGrid";

const BentoRow = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn("flex h-[600px] w-full items-center gap-4", className)} {...props}>
      {children}
    </div>
  )
);
BentoRow.displayName = "BentoRow";

const BentoItem = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    width?: "full" | "half" | "auto";
  }
>(({ className, width = "auto", children, ...props }, ref) => {
  const widthClasses = {
    full: "w-full",
    half: "w-[560px] min-w-[360px]",
    auto: "flex-1 min-w-[360px]",
  };

  return (
    <div
      ref={ref}
      className={cn(
        "flex h-full flex-col items-start overflow-hidden rounded-xl border border-[rgba(250,250,250,0.2)] bg-[rgba(9,9,11,0.8)]",
        widthClasses[width],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});
BentoItem.displayName = "BentoItem";

const BentoItemSmall = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex h-[560px] min-w-[360px] flex-col items-start gap-6 overflow-hidden rounded-xl border border-[rgba(250,250,250,0.2)] bg-[rgba(9,9,11,0.8)] px-6 py-6",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
);
BentoItemSmall.displayName = "BentoItemSmall";

export { BentoGrid, BentoItem, BentoItemSmall, BentoRow };
