import React from "react";

import { cn } from "../../lib/utils";
import { Button } from "./button";

interface NavbarProps extends React.HTMLAttributes<HTMLElement> {
  logo?: React.ReactNode;
  navigationItems?: {
    label: string;
    href?: string;
    hasDropdown?: boolean;
  }[];
  ctaItems?: {
    label: string;
    variant?: "default" | "secondary";
    href?: string;
  }[];
}

const Navbar = React.forwardRef<HTMLElement, NavbarProps>(
  ({ className, logo, navigationItems = [], ctaItems = [], ...props }, ref) => (
    <nav
      ref={ref}
      className={cn(
        "relative mx-auto flex max-w-[1312px] items-center justify-between bg-black px-8 py-4",
        className
      )}
      {...props}
    >
      <div className="flex items-center justify-center gap-4">
        {logo}

        {navigationItems.map((item, index) => (
          <div
            key={index}
            className="flex items-center justify-center gap-2 rounded-md px-2 py-2 transition-colors hover:bg-[rgba(250,250,250,0.05)]"
          >
            <span className="font-inter text-sm leading-5 font-normal text-[#FAFAFA]">
              {item.label}
            </span>
            {item.hasDropdown && (
              <svg
                width="12"
                height="12"
                viewBox="0 0 12 12"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M3 4.5L6 7.5L9 4.5"
                  stroke="#FAFAFA"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </div>
        ))}
      </div>

      <div className="flex items-start justify-center gap-4">
        {ctaItems.map((item, index) => (
          <Button key={index} variant={item.variant ?? "secondary"} asChild={!!item.href}>
            {item.href ? <a href={item.href}>{item.label}</a> : item.label}
          </Button>
        ))}
      </div>
    </nav>
  )
);
Navbar.displayName = "Navbar";

const NavbarLogo = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn("flex w-[116px] items-center gap-2", className)} {...props}>
      {children}
    </div>
  )
);
NavbarLogo.displayName = "NavbarLogo";

const NavbarLogoIcon = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "relative flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-[4px] p-0",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
);
NavbarLogoIcon.displayName = "NavbarLogoIcon";

const NavbarLogoText = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("font-inter text-center text-lg leading-7 font-bold text-[#FAFAFA]", className)}
      {...props}
    >
      {children}
    </div>
  )
);
NavbarLogoText.displayName = "NavbarLogoText";

export { Navbar, NavbarLogo, NavbarLogoIcon, NavbarLogoText };
