/**
 * Formatting utilities for display values throughout the UI.
 * All functions are pure — no side effects, no hooks.
 */

/** Formats milliseconds into a human-readable duration (e.g. "2m 30s"). */
export function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;
  return `${minutes}m ${remaining}s`;
}

/** Formats an ISO date string into "Mar 5, 02:30 PM" style. */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Formats a USD value with two decimal places (e.g. "$1.50"). */
export function formatCurrency(usd: number): string {
  return `$${usd.toFixed(2)}`;
}

/** Formats seconds into "M:SS" timestamp format for shot timecodes. */
export function formatSeconds(s: number): string {
  const mins = Math.floor(s / 60);
  const secs = Math.floor(s % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

/** Formats bytes into a readable file size (e.g. "2.5 MB", "512 KB"). Returns em-dash for 0. */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "\u2014";
  const mb = bytes / (1024 * 1024);
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`;
}

/**
 * Formats a Ken Burns camera config into a human-readable string.
 * Returns em-dash if no config is provided.
 */
export function formatKenBurns(config: Record<string, unknown> | null | undefined): string {
  if (!config) return "\u2014";
  const direction = String(config.direction ?? "").replace("_", " ");
  const scale = config.scale ? `${config.scale}x` : "";
  return `${direction} ${scale}`.trim() || "\u2014";
}
