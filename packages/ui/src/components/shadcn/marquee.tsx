"use client";

import type { HTMLAttributes } from "react";
import * as React from "react";
import type { MarqueeProps as FastMarqueeProps } from "react-fast-marquee";
import FastMarquee from "react-fast-marquee";

export type MarqueeProps = HTMLAttributes<HTMLDivElement>;

export const Marquee = ({ className, ...props }: MarqueeProps) => (
  <div className={`relative w-full overflow-hidden ${className ?? ""}`} {...props} />
);

export type MarqueeContentProps = FastMarqueeProps;

export const MarqueeContent = ({
  loop = 0,
  autoFill = true,
  pauseOnHover = true,
  ...props
}: MarqueeContentProps) => {
  const MarqueeComponent = FastMarquee as React.ComponentType<FastMarqueeProps>;
  return (
    <MarqueeComponent autoFill={autoFill} loop={loop} pauseOnHover={pauseOnHover} {...props} />
  );
};

export type MarqueeFadeProps = HTMLAttributes<HTMLDivElement> & {
  side: "left" | "right";
};

export const MarqueeFade = ({ className, side, ...props }: MarqueeFadeProps) => (
  <div
    className={`absolute top-0 bottom-0 z-10 h-full w-24 ${
      side === "left"
        ? "left-0 bg-gradient-to-r from-gray-900 to-transparent"
        : "right-0 bg-gradient-to-l from-gray-900 to-transparent"
    } ${className ?? ""}`}
    {...props}
  />
);

export type MarqueeItemProps = HTMLAttributes<HTMLDivElement>;

export const MarqueeItem = ({ className, ...props }: MarqueeItemProps) => (
  <div className={`mx-2 flex-shrink-0 object-contain ${className ?? ""}`} {...props} />
);
