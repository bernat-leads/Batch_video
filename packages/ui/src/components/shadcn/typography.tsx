import React from "react";

import { cn } from "../../lib/utils";

const H1 = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h1
      ref={ref}
      className={cn(
        "font-inter w-[1248px] bg-gradient-to-r from-[#FAFAFA] to-[#A1A1AA] bg-clip-text text-center text-[96px] leading-[96px] font-bold text-transparent",
        className
      )}
      {...props}
    />
  )
);
H1.displayName = "H1";

const H2 = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h2
      ref={ref}
      className={cn("font-inter text-5xl leading-[48px] font-bold text-[#FAFAFA]", className)}
      {...props}
    />
  )
);
H2.displayName = "H2";

const H3 = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn("font-inter text-2xl leading-8 font-bold text-[#FAFAFA]", className)}
      {...props}
    />
  )
);
H3.displayName = "H3";

const P = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn("font-inter text-base leading-6 font-normal text-[#A1A1AA]", className)}
      {...props}
    />
  )
);
P.displayName = "P";

const PLarge = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn("font-inter text-xl leading-7 font-normal text-[#A1A1AA]", className)}
      {...props}
    />
  )
);
PLarge.displayName = "PLarge";

const PSmall = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn("font-inter text-sm leading-5 font-normal text-[#A1A1AA]", className)}
      {...props}
    />
  )
);
PSmall.displayName = "PSmall";

const Label = React.forwardRef<HTMLSpanElement, React.HTMLAttributes<HTMLSpanElement>>(
  ({ className, ...props }, ref) => (
    <span
      ref={ref}
      className={cn("font-inter text-sm leading-5 font-bold text-[#FAFAFA]", className)}
      {...props}
    />
  )
);
Label.displayName = "Label";

export { H1, H2, H3, Label, P, PLarge, PSmall };
