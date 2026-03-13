import { cva } from "class-variance-authority";
import type { VariantProps } from "class-variance-authority";

import { cn } from "../lib/utils";

const visual3dVariants = cva("relative flex items-center justify-center", {
  variants: {
    variant: {
      globe: "h-24 w-24",
      rocket: "h-20 w-20",
      grid: "h-28 w-28",
      chat: "h-20 w-32",
    },
    size: {
      sm: "scale-75",
      md: "scale-100",
      lg: "scale-125",
    },
  },
  defaultVariants: {
    variant: "globe",
    size: "md",
  },
});

export interface Visual3DProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof visual3dVariants> {}

export function Visual3D({ className, variant, size, ...props }: Visual3DProps) {
  const renderVisual = () => {
    switch (variant) {
      case "globe":
        return (
          <div className="relative h-full w-full">
            {/* Glowing orange wireframe globe */}
            <div className="absolute inset-0 rounded-full border-2 border-orange-500/60 bg-gradient-to-br from-orange-500/10 to-transparent" />
            {/* Grid lines with orange glow */}
            <div className="absolute inset-0 rounded-full border border-orange-500/40" />
            <div className="absolute top-1/2 right-0 left-0 h-px bg-gradient-to-r from-transparent via-orange-500/60 to-transparent" />
            <div className="absolute top-0 bottom-0 left-1/2 w-px bg-gradient-to-b from-transparent via-orange-500/60 to-transparent" />
            {/* Additional grid lines */}
            <div className="absolute top-1/4 right-0 left-0 h-px bg-gradient-to-r from-transparent via-orange-500/40 to-transparent" />
            <div className="absolute right-0 bottom-1/4 left-0 h-px bg-gradient-to-r from-transparent via-orange-500/40 to-transparent" />
            <div className="absolute top-0 bottom-0 left-1/4 w-px bg-gradient-to-b from-transparent via-orange-500/40 to-transparent" />
            <div className="absolute top-0 right-1/4 bottom-0 w-px bg-gradient-to-b from-transparent via-orange-500/40 to-transparent" />
            {/* Glow effect */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-br from-orange-500/30 via-transparent to-transparent blur-sm" />
          </div>
        );

      case "rocket":
        return (
          <div className="relative h-full w-full">
            {/* Paper airplane icon on textured background */}
            <div className="absolute inset-0 rounded-full border-2 border-amber-600 bg-gradient-to-br from-amber-700 to-amber-800">
              {/* Concentric circles */}
              <div className="absolute inset-2 rounded-full border border-amber-500/50" />
              <div className="absolute inset-4 rounded-full border border-amber-500/30" />
              <div className="absolute inset-6 rounded-full border border-amber-500/20" />
            </div>
            {/* Paper airplane */}
            <div className="absolute inset-0 flex items-center justify-center">
              <svg className="h-8 w-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            </div>
          </div>
        );

      case "grid":
        return (
          <div className="relative h-full w-full">
            {/* Technology stack icons */}
            <div className="grid grid-cols-3 gap-2">
              {/* Lightning bolt */}
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-700">
                <svg className="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              {/* Database */}
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-700">
                <svg className="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 12v3c0 1.657 3.134 3 7 3s7-1.343 7-3v-3c0 1.657-3.134 3-7 3s-7-1.343-7-3z" />
                  <path d="M3 7v3c0 1.657 3.134 3 7 3s7-1.343 7-3V7c0 1.657-3.134 3-7 3S3 8.657 3 7z" />
                  <path d="M17 5c0 1.657-3.134 3-7 3S3 6.657 3 5s3.134-3 7-3 7 1.343 7 3z" />
                </svg>
              </div>
              {/* Gear */}
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-700">
                <svg className="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c.836 1.372 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.372-.836 1.372-2.942-.734-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              {/* Code brackets */}
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-700">
                <svg className="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              {/* TypeScript TS */}
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-700">
                <span className="text-xs font-bold text-white">TS</span>
              </div>
              {/* Empty space */}
              <div className="h-8 w-8"></div>
            </div>
          </div>
        );

      case "chat":
        return (
          <div className="relative h-full w-full">
            {/* Chat interface with CMS interaction */}
            <div className="space-y-3">
              {/* First message */}
              <div className="max-w-xs rounded-lg bg-slate-700 p-3">
                <div className="mb-1 text-xs text-slate-300">Scott G.</div>
                <div className="text-sm text-white">
                  We need to update this heading before launch.
                </div>
              </div>
              {/* Second message with button */}
              <div className="ml-4 max-w-xs rounded-lg bg-slate-700 p-3">
                <div className="mb-1 text-xs text-slate-300">Eric D.</div>
                <div className="mb-2 text-sm text-white">
                  Let me quickly jump into Sanity and fix it
                </div>
                <button className="rounded bg-green-600 px-3 py-1 text-xs text-white">Done!</button>
              </div>
            </div>
          </div>
        );

      default:
        return (
          <div className="bg-muted flex h-full w-full items-center justify-center rounded-lg">
            <span className="text-muted-foreground text-2xl">✨</span>
          </div>
        );
    }
  };

  return (
    <div className={cn(visual3dVariants({ variant, size, className }))} {...props}>
      {renderVisual()}
    </div>
  );
}
