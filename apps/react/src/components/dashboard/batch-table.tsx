import { useState, useRef, useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  createColumnHelper,
  flexRender,
  type SortingState,
  type RowSelectionState,
} from "@tanstack/react-table";
import { ArrowUpDown, Download, MoreHorizontal, Pencil, Search, Trash2 } from "lucide-react";
import type { BatchRead } from "@packages/api-client";
import { Checkbox } from "@packages/ui/components/shadcn/checkbox";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@packages/ui/components/shadcn/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@packages/ui/components/shadcn/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@packages/ui/components/shadcn/table";
import { cn } from "@packages/ui/lib/utils";
import { ConfirmDeleteDialog } from "@/components/ui/confirm-delete-dialog";
import { formatDate } from "@/lib/format";
import { TablePagination } from "./table-pagination";

const columnHelper = createColumnHelper<BatchRead>();

function BatchActions({
  batch,
  onRename,
  onDelete,
}: {
  batch: BatchRead;
  onRename: () => void;
  onDelete?: (batchId: string) => void;
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="inline-flex h-8 w-8 items-center justify-center rounded-md transition-colors hover:bg-black/5"
          onClick={(e) => e.stopPropagation()}
        >
          <MoreHorizontal size={16} className="text-text-muted" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="bg-card-bg border-border"
      >
        <DropdownMenuItem
          onClick={(e) => {
            e.stopPropagation();
            onRename();
          }}
          className="text-text-secondary"
        >
          <Pencil size={14} className="mr-2" />
          Rename
        </DropdownMenuItem>
        <DropdownMenuItem
          disabled
          onClick={(e) => {
            e.stopPropagation();
            // TODO: implement export
          }}
          className="text-text-secondary"
        >
          <Download size={14} className="mr-2" />
          Export
        </DropdownMenuItem>
        <ConfirmDeleteDialog
          title="Delete batch?"
          description="This batch and all its videos will be permanently deleted."
          onConfirm={() => onDelete?.(batch.id)}
        >
          <DropdownMenuItem
            onSelect={(e) => e.preventDefault()}
            onClick={(e) => e.stopPropagation()}
            className="text-status-error"
          >
            <Trash2 size={14} className="mr-2" />
            Delete
          </DropdownMenuItem>
        </ConfirmDeleteDialog>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function RenameBatchDialog({
  batch,
  open,
  onOpenChange,
  onSave,
}: {
  batch: BatchRead | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (id: string, newName: string) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [value, setValue] = useState("");

  useEffect(() => {
    if (open && batch) {
      setValue(batch.name);
      setTimeout(() => {
        inputRef.current?.focus();
        inputRef.current?.select();
      }, 0);
    }
  }, [open, batch]);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (trimmed && batch) {
      onSave(batch.id, trimmed);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-sm [&>button[data-slot=dialog-close]]:hidden bg-card-bg border-border"
      >
        <DialogHeader>
          <DialogTitle className="text-text-primary">
            Rename Batch
          </DialogTitle>
        </DialogHeader>
        <input
          ref={inputRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSubmit();
          }}
          className="h-9 w-full rounded-lg border px-3 text-sm outline-none text-text-primary border-border bg-content-bg"
          placeholder="Batch name"
        />
        <div className="flex justify-end gap-2">
          <button
            onClick={() => onOpenChange(false)}
            className="h-9 rounded-lg border px-4 text-sm font-medium transition-colors hover:bg-black/5 border-border text-text-secondary"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="h-9 rounded-lg px-4 text-sm font-medium text-white transition-colors hover:opacity-90 bg-brand"
          >
            Rename
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

interface PaginationInfo {
  page: number;
  totalPages: number;
  total: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
}

interface BatchTableProps {
  batches: BatchRead[];
  toolbar?: React.ReactNode;
  pagination?: PaginationInfo;
  onSelectionChange?: (selectedBatches: BatchRead[]) => void;
  onRename?: (id: string, newName: string) => void;
  onDelete?: (batchId: string) => void;
}

export function BatchTable({ batches, toolbar, pagination, onSelectionChange, onRename, onDelete }: BatchTableProps) {
  const navigate = useNavigate();
  const [sorting, setSorting] = useState<SortingState>([]);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [globalFilter, setGlobalFilter] = useState("");
  const [renamingBatch, setRenamingBatch] = useState<BatchRead | null>(null);

  const columns = [
    columnHelper.accessor("name", {
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
    columnHelper.display({
      id: "status",
      header: "Progress",
      cell: ({ row }) => {
        const b = row.original;
        return (
          <span className="text-sm text-text-secondary">
            {b.completed_count}/{b.total_videos} done
          </span>
        );
      },
    }),
    columnHelper.accessor("total_cost_usd", {
      header: "Cost",
      cell: (info) => {
        const val = info.getValue() ?? 0;
        return (
          <span className="text-sm text-text-secondary">
            {val > 0 ? `$${val.toFixed(2)}` : "\u2014"}
          </span>
        );
      },
    }),
    columnHelper.accessor("created_at", {
      header: "Created",
      cell: (info) => (
        <span className="text-sm text-text-muted">
          {formatDate(info.getValue())}
        </span>
      ),
    }),
    columnHelper.display({
      id: "actions",
      header: "",
      cell: ({ row }) => (
        <div onClick={(e) => e.stopPropagation()}>
          <BatchActions
            batch={row.original}
            onRename={() => setRenamingBatch(row.original)}
            onDelete={onDelete}
          />
        </div>
      ),
      enableSorting: false,
    }),
  ];

  const table = useReactTable({
    data: batches,
    columns,
    state: { sorting, rowSelection, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    onRowSelectionChange: (updater) => {
      const next = typeof updater === "function" ? updater(rowSelection) : updater;
      setRowSelection(next);
      if (onSelectionChange) {
        const selected = Object.keys(next)
          .filter((k) => next[k])
          .map((k) => batches[Number(k)])
          .filter((b): b is BatchRead => b !== undefined);
        onSelectionChange(selected);
      }
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    enableRowSelection: true,
  });

  return (
    <div>
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="relative">
          <Search
            size={15}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted"
          />
          <input
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            placeholder="Search batches..."
            className="h-9 w-64 rounded-lg border pl-9 pr-3 text-sm outline-none border-border bg-card-bg text-text-primary"
          />
        </div>
        {toolbar}
      </div>
      <div className="overflow-hidden rounded-xl border border-border bg-card-bg">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow
                key={headerGroup.id}
                className="border-border bg-content-bg"
              >
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className={cn(
                      "text-text-secondary",
                      header.column.getCanSort() && "cursor-pointer select-none",
                    )}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    {header.column.id === "select" || header.column.id === "actions" ? (
                      flexRender(header.column.columnDef.header, header.getContext())
                    ) : (
                      <div className="flex items-center gap-1">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {header.column.getCanSort() && (
                          <ArrowUpDown size={12} className="opacity-40" />
                        )}
                      </div>
                    )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                className="cursor-pointer border-border"
                data-state={row.getIsSelected() ? "selected" : undefined}
                onClick={() =>
                  navigate({
                    to: "/app/batches/$batchId",
                    params: { batchId: row.original.id },
                  })
                }
              >
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {pagination && (
        <TablePagination
          page={pagination.page}
          totalPages={pagination.totalPages}
          total={pagination.total}
          pageSize={pagination.pageSize}
          onPageChange={pagination.onPageChange}
          onPageSizeChange={pagination.onPageSizeChange}
        />
      )}
      <RenameBatchDialog
        batch={renamingBatch}
        open={renamingBatch !== null}
        onOpenChange={(open) => {
          if (!open) setRenamingBatch(null);
        }}
        onSave={(id, newName) => onRename?.(id, newName)}
      />
    </div>
  );
}
