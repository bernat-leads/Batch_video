import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@packages/ui/lib/utils";

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

interface TablePaginationProps {
  page: number;
  totalPages: number;
  total: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
}

/** Pagination controls with page numbers, prev/next buttons, and page size selector. */
export function TablePagination({
  page,
  totalPages,
  total,
  pageSize,
  onPageChange,
  onPageSizeChange,
}: TablePaginationProps) {
  if (totalPages <= 1 && !onPageSizeChange) return null;

  const start = Math.min((page - 1) * pageSize + 1, total);
  const end = Math.min(page * pageSize, total);

  const pages = getVisiblePages(page, totalPages);

  return (
    <div className="mt-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <p className="text-xs text-text-muted">
          {total > 0 ? `${start}–${end} of ${total}` : "0 results"}
        </p>
        {onPageSizeChange && (
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="h-8 rounded-md border border-border bg-card-bg px-2 text-sm text-text-secondary outline-none"
          >
            {PAGE_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size}>
                {size} / page
              </option>
            ))}
          </select>
        )}
      </div>
      {totalPages > 1 && (
        <div className="flex items-center gap-1">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-text-secondary transition-colors hover:bg-content-bg disabled:pointer-events-none disabled:opacity-40"
          >
            <ChevronLeft size={16} />
          </button>
          {pages.map((p, i) =>
            p === "..." ? (
              <span
                key={`ellipsis-${i}`}
                className="inline-flex h-8 w-8 items-center justify-center text-xs text-text-muted"
              >
                ...
              </span>
            ) : (
              <button
                key={p}
                onClick={() => onPageChange(p)}
                className={cn(
                  "inline-flex h-8 w-8 items-center justify-center rounded-md text-sm transition-colors",
                  p === page
                    ? "bg-brand text-white"
                    : "text-text-secondary hover:bg-content-bg",
                )}
              >
                {p}
              </button>
            ),
          )}
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-text-secondary transition-colors hover:bg-content-bg disabled:pointer-events-none disabled:opacity-40"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * Computes which page numbers to show in the pagination bar.
 * Shows first, last, and a window around current page with ellipses.
 */
function getVisiblePages(
  current: number,
  total: number,
): (number | "...")[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  if (current <= 3) {
    return [1, 2, 3, 4, "...", total];
  }

  if (current >= total - 2) {
    return [1, "...", total - 3, total - 2, total - 1, total];
  }

  return [1, "...", current - 1, current, current + 1, "...", total];
}
