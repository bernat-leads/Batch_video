import * as React from "react";
import { X } from "lucide-react";

export interface ToastProps {
  message: string;
  type: "error" | "success";
  isVisible: boolean;
  onClose: () => void;
}

export type ToastActionElement = React.ReactElement;

// Shadcn-style toast components
export const ToastProvider = React.createContext({});

export const Toast = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
  }
>(({ className, open = true, onOpenChange: _onOpenChange, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={`bg-background fixed top-4 right-4 z-50 rounded-lg border p-4 shadow-lg ${className ?? ""}`}
      style={{ display: open ? "block" : "none" }}
      {...props}
    />
  );
});

export const ToastClose = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ className, ...props }, ref) => (
  <button
    ref={ref}
    className={`text-foreground/50 hover:text-foreground absolute top-2 right-2 rounded-md p-1 opacity-0 transition-opacity group-hover:opacity-100 focus:opacity-100 focus:ring-2 focus:outline-none ${className ?? ""}`}
    {...props}
  >
    <X className="h-4 w-4" />
  </button>
));

export const ToastTitle = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={`text-sm font-semibold ${className ?? ""}`} {...props} />
  )
);

export const ToastDescription = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={`text-sm opacity-90 ${className ?? ""}`} {...props} />
));

export const ToastViewport = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={`fixed top-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:top-auto sm:right-0 sm:bottom-0 sm:flex-col md:max-w-[420px] ${className ?? ""}`}
      {...props}
    />
  )
);

// Keep the original custom toast for backward compatibility
export function CustomToast({ message, type, isVisible, onClose }: ToastProps) {
  React.useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => {
        onClose();
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [isVisible, onClose]);

  if (!isVisible) return null;

  const bgColor = type === "error" ? "bg-red-500" : "bg-green-500";
  const textColor = "text-white";

  return (
    <div className="animate-in slide-in-from-top-2 fixed top-4 right-4 z-50">
      <div className={`${bgColor} ${textColor} max-w-sm rounded-lg p-4 shadow-lg`}>
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium">{message}</p>
          <button
            onClick={onClose}
            className="ml-4 text-white/80 transition-colors hover:text-white"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
