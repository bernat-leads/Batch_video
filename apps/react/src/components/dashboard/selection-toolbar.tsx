import { Download, Trash2 } from "lucide-react";
import { ConfirmDeleteDialog } from "@/components/ui/confirm-delete-dialog";

interface SelectionToolbarProps {
  count: number;
  onExport: () => void;
  onDelete: () => void;
}

export function SelectionToolbar({ count, onExport, onDelete }: SelectionToolbarProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-text-muted">{count} selected</span>
      <button
        className="inline-flex h-9 items-center gap-2 rounded-lg border border-border px-3 text-sm font-medium text-text-secondary transition-colors hover:bg-black/5"
        onClick={onExport}
      >
        <Download size={15} />
        Export
      </button>
      <ConfirmDeleteDialog
        title={`Delete ${count} item${count > 1 ? "s" : ""}?`}
        description="This action cannot be undone. All selected items will be permanently deleted."
        onConfirm={onDelete}
      >
        <button
          className="inline-flex h-9 items-center gap-2 rounded-lg bg-status-error px-3 text-sm font-medium text-white transition-colors hover:opacity-90"
        >
          <Trash2 size={15} />
          Delete
        </button>
      </ConfirmDeleteDialog>
    </div>
  );
}
