import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { createColumnHelper } from "@tanstack/react-table";
import { Download, Loader2, MoreHorizontal, Trash2 } from "lucide-react";
import type { BatchRead } from "@packages/api-client";
import { Checkbox } from "@packages/ui/components/shadcn/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@packages/ui/components/shadcn/dropdown-menu";
import { ConfirmDeleteDialog } from "@/components/ui/confirm-delete-dialog";
import { exportBatchZip } from "@/lib/download";
import { formatDate, formatCurrency } from "@/lib/format";
import type { PaginationInfo } from "@/lib/types";
import { DataTable } from "./data-table";
import { StatusBadge } from "./status-badge";

const col = createColumnHelper<BatchRead>();

/** Dropdown menu with export and delete actions for a single batch row. */
function BatchActions({
  batch,
  onDelete,
}: {
  batch: BatchRead;
  onDelete: () => void;
}) {
  const [exporting, setExporting] = useState(false);

  const handleExport = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setExporting(true);
    try {
      await exportBatchZip(batch.id, batch.name);
    } finally {
      setExporting(false);
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="inline-flex h-8 w-8 items-center justify-center rounded-md transition-colors hover:bg-black/5"
          onClick={(e) => e.stopPropagation()}
        >
          {exporting ? (
            <Loader2 size={16} className="animate-spin text-text-muted" />
          ) : (
            <MoreHorizontal size={16} className="text-text-muted" />
          )}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="bg-card-bg border-border">
        <DropdownMenuItem
          disabled={(batch.completed_count ?? 0) === 0 || exporting}
          onClick={handleExport}
          className="text-text-secondary"
        >
          {exporting ? (
            <Loader2 size={14} className="mr-2 animate-spin" />
          ) : (
            <Download size={14} className="mr-2" />
          )}
          {exporting ? "Exporting..." : "Export"}
        </DropdownMenuItem>
        <ConfirmDeleteDialog
          title="Delete batch?"
          description="This will permanently delete the batch and all its videos. This action cannot be undone."
          onConfirm={onDelete}
        >
          <DropdownMenuItem
            onSelect={(e) => e.preventDefault()}
            className="text-status-error focus:text-status-error"
          >
            <Trash2 size={14} className="mr-2" />
            Delete
          </DropdownMenuItem>
        </ConfirmDeleteDialog>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

/** Column definitions for the batch data table. */
function getBatchColumns(onDelete?: (id: string) => void) {
  return [
    col.accessor("name", {
      id: "select",
      header: ({ table }) => (
        <label className="flex items-center gap-3 cursor-pointer">
          <Checkbox
            checked={
              table.getIsAllPageRowsSelected() ||
              (table.getIsSomePageRowsSelected() && "indeterminate")
            }
            onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
            aria-label="Select all"
          />
          <span>Name</span>
        </label>
      ),
      cell: ({ row }) => (
        <label
          className="flex items-center gap-3 cursor-pointer"
          onClick={(e) => e.stopPropagation()}
        >
          <Checkbox
            checked={row.getIsSelected()}
            onCheckedChange={(value) => row.toggleSelected(!!value)}
            aria-label="Select row"
          />
          <span className="text-sm font-medium text-text-primary">
            {row.original.name}
          </span>
        </label>
      ),
      enableSorting: false,
    }),
    col.display({
      id: "status",
      header: "Status",
      cell: ({ row }) => <StatusBadge status={row.original.status} />,
    }),
    col.display({
      id: "progress",
      header: "Progress",
      cell: ({ row }) => (
        <span className="text-sm text-text-secondary">
          {row.original.completed_count}/{row.original.total_videos} done
        </span>
      ),
    }),
    col.display({
      id: "cost",
      header: "Cost",
      cell: ({ row }) => {
        const val = row.original.total?.cost_usd ?? 0;
        return (
          <span className="text-sm text-text-secondary">
            {val > 0 ? formatCurrency(val) : "\u2014"}
          </span>
        );
      },
    }),
    col.accessor("created_at", {
      header: "Created",
      cell: (info) => (
        <span className="text-sm text-text-muted">
          {formatDate(info.getValue())}
        </span>
      ),
    }),
    col.display({
      id: "actions",
      header: "",
      cell: ({ row }) => (
        <div onClick={(e) => e.stopPropagation()}>
          <BatchActions
            batch={row.original}
            onDelete={() => onDelete?.(row.original.id)}
          />
        </div>
      ),
      enableSorting: false,
    }),
  ];
}

interface BatchTableProps {
  batches: BatchRead[];
  toolbar?: React.ReactNode;
  pagination?: PaginationInfo;
  onSelectionChange?: (selectedBatches: BatchRead[]) => void;
  onDelete?: (id: string) => void;
}

/**
 * Sortable, selectable data table for batch listings.
 * Delegates rendering to the generic DataTable component.
 */
export function BatchTable({ batches, toolbar, pagination, onSelectionChange, onDelete }: BatchTableProps) {
  const navigate = useNavigate();

  return (
    <DataTable
      data={batches}
      columns={getBatchColumns(onDelete)}
      searchPlaceholder="Search batches..."
      toolbar={toolbar}
      pagination={pagination}
      onSelectionChange={onSelectionChange}
      onRowClick={(batch) =>
        navigate({ to: "/app/batches/$batchId", params: { batchId: batch.id } })
      }
    />
  );
}
