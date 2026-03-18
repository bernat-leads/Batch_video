import { useState } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@packages/ui/lib/utils";

interface AsyncButtonProps {
  onClick: () => Promise<void> | void;
  icon?: React.ReactNode;
  label: string;
  loadingLabel?: string;
  disabled?: boolean;
  className?: string;
}

/** Button that shows a spinner while its async onClick runs. */
export function AsyncButton({
  onClick,
  icon,
  label,
  loadingLabel,
  disabled = false,
  className,
}: AsyncButtonProps) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      await onClick();
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      className={cn(
        "inline-flex h-9 items-center gap-2 rounded-lg border border-border bg-card-bg px-3 text-sm font-medium text-text-secondary transition-colors hover:bg-content-bg disabled:opacity-50",
        className,
      )}
      onClick={handleClick}
      disabled={disabled || loading}
    >
      {loading ? <Loader2 size={15} className="animate-spin" /> : icon}
      {loading ? (loadingLabel ?? label) : label}
    </button>
  );
}
