import React from "react";

import { cn } from "../../lib/utils";
import { Label } from "./typography";

interface LogoItem {
  icon: React.ReactNode;
  name: string;
  version?: string;
}

interface LogosSectionProps extends React.HTMLAttributes<HTMLElement> {
  title: string;
  logos: LogoItem[];
}

const LogosSection = React.forwardRef<HTMLElement, LogosSectionProps>(
  ({ className, title, logos, ...props }, ref) => (
    <section
      ref={ref}
      className={cn(
        "mx-auto flex max-w-[1312px] flex-col items-center gap-12 px-8 py-20",
        className
      )}
      {...props}
    >
      <Label className="text-center">{title}</Label>

      <div className="flex w-full flex-wrap content-center items-center justify-center gap-6 md:gap-12">
        {logos.map((logo, index) => (
          <div key={index} className="flex items-center gap-2">
            {logo.icon}
            <div className="font-inter text-sm leading-5 font-normal text-[#FAFAFA]">
              {logo.name}
            </div>
            {logo.version && (
              <div className="font-inter text-sm leading-5 font-normal text-[#A1A1AA]">
                {logo.version}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  )
);
LogosSection.displayName = "LogosSection";

export { LogosSection };
export type { LogoItem };
