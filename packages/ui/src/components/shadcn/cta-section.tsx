import React from "react";

import { cn } from "../../lib/utils";
import { Button } from "./button";
import { H2 } from "./typography";

interface CTAItem {
  text: string;
  variant?: "default" | "secondary";
  href?: string;
}

interface CTASectionProps extends React.HTMLAttributes<HTMLElement> {
  title: string;
  ctas: CTAItem[];
  showGlows?: boolean;
}

const CTASection = React.forwardRef<HTMLElement, CTASectionProps>(
  ({ className, title, ctas, showGlows = false, ...props }, ref) => (
    <section
      ref={ref}
      className={cn(
        "relative mx-auto flex max-w-[1312px] flex-col items-center gap-24 px-8 py-0",
        className
      )}
      {...props}
    >
      <div className="flex w-full flex-col items-center gap-12 px-0 py-32">
        <H2 className="w-full text-center">{title}</H2>

        <div className="flex items-start gap-4">
          {ctas.map((cta, index) => (
            <Button key={index} variant={cta.variant ?? "default"} asChild={!!cta.href}>
              {cta.href ? <a href={cta.href}>{cta.text}</a> : cta.text}
            </Button>
          ))}
        </div>
      </div>

      {showGlows && (
        <svg
          width="1312"
          height="280"
          viewBox="0 0 1312 280"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="absolute bottom-0 h-[280px] w-[1312px]"
        >
          <g clipPath="url(#clip0_2029_6723)">
            <g filter="url(#filter0_f_2029_6723)">
              <ellipse cx="656" cy="442.5" rx="481.5" ry="144.5" fill="#fbbf24" fillOpacity="0.6" />
            </g>
            <g filter="url(#filter1_f_2029_6723)">
              <ellipse cx="656" cy="377" rx="481.5" ry="74" fill="#fbbf24" />
            </g>
          </g>
          <defs>
            <filter
              id="filter0_f_2029_6723"
              x="-137.5"
              y="-14"
              width="1587"
              height="913"
              filterUnits="userSpaceOnUse"
              colorInterpolationFilters="sRGB"
            >
              <feFlood floodOpacity="0" result="BackgroundImageFix" />
              <feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape" />
              <feGaussianBlur stdDeviation="156" result="effect1_foregroundBlur_2029_6723" />
            </filter>
            <filter
              id="filter1_f_2029_6723"
              x="110.5"
              y="239"
              width="1091"
              height="276"
              filterUnits="userSpaceOnUse"
              colorInterpolationFilters="sRGB"
            >
              <feFlood floodOpacity="0" result="BackgroundImageFix" />
              <feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape" />
              <feGaussianBlur stdDeviation="32" result="effect1_foregroundBlur_2029_6723" />
            </filter>
            <clipPath id="clip0_2029_6723">
              <rect width="1312" height="280" fill="white" />
            </clipPath>
          </defs>
        </svg>
      )}
    </section>
  )
);
CTASection.displayName = "CTASection";

export { CTASection };
export type { CTAItem };
