import { Download, RotateCcw, Trash2 } from "lucide-react";
import { AsyncButton } from "@/components/ui/async-button";
import { ConfirmDeleteDialog } from "@/components/ui/confirm-delete-dialog";

interface SelectionToolbarProps {
  count: number;
  onExport: () => Promise<void> | void;
  exportLabel?: string;
  onDelete?: () => void;
  onRetry?: () => Promise<void> | void;
  retryCount?: number;
}

/** Action bar shown when rows are selected in a table. Provides export, retry, and bulk delete. */
export function SelectionToolbar({ count, onExport, exportLabel = "Export", onDelete, onRetry, retryCount }: SelectionToolbarProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-text-muted">{count} selected</span>
      <AsyncButton
        onClick={onExport}
        icon={<Download size={15} />}
        label={exportLabel}
        loadingLabel="Exporting..."
      />
      {onRetry && !!retryCount && (
        <AsyncButton
          onClick={onRetry}
          icon={<RotateCcw size={15} />}
          label={`Retry ${retryCount} Failed`}
          loadingLabel="Retrying..."
        />
      )}
      {onDelete && (
        <ConfirmDeleteDialog
          title={`Delete ${count} batch${count > 1 ? "es" : ""}?`}
          description="This will permanently delete the selected batches and all their videos. This action cannot be undone."
          onConfirm={onDelete}
        >
          <button className="inline-flex h-9 items-center gap-2 rounded-lg border border-border bg-card-bg px-3 text-sm font-medium text-status-error transition-colors hover:bg-status-error-light">
            <Trash2 size={15} />
            Delete
          </button>
        </ConfirmDeleteDialog>
      )}
    </div>
  );
}
