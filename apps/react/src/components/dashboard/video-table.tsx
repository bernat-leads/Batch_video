import { useState } from "react";
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
import { ArrowUpDown, Download, Film, MoreHorizontal, Play, Search, Trash2 } from "lucide-react";
import type { VideoRead } from "@packages/api-client";
import { Checkbox } from "@packages/ui/components/shadcn/checkbox";
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
import { formatDate, formatDuration } from "@/lib/format";
import { StatusBadge } from "./status-badge";
import { TablePagination } from "./table-pagination";

const columnHelper = createColumnHelper<VideoRead>();

function VideoActions({ video, onDelete }: { video: VideoRead; onDelete?: (videoId: string) => void }) {
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
        {video.status === "completed" && video.output_url && (
          <DropdownMenuItem
            onClick={(e) => {
              e.stopPropagation();
              window.open(video.output_url!, "_blank");
            }}
            className="text-text-secondary"
          >
            <Download size={14} className="mr-2" />
            Download
          </DropdownMenuItem>
        )}
        <ConfirmDeleteDialog
          title="Delete video?"
          description="This video and all its shots will be permanently deleted."
          onConfirm={() => onDelete?.(video.id)}
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

interface BatchInfo {
  name: string;
  fileName: string;
}

interface PaginationInfo {
  page: number;
  totalPages: number;
  total: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
}

interface VideoTableProps {
  videos: VideoRead[];
  batches?: Record<string, BatchInfo>;
  showIndex?: boolean;
  toolbar?: React.ReactNode;
  pagination?: PaginationInfo;
  onSelectionChange?: (selected: VideoRead[]) => void;
  onDelete?: (videoId: string) => void;
}

export function VideoTable({ videos, batches, showIndex = true, toolbar, pagination, onSelectionChange, onDelete }: VideoTableProps) {
  const navigate = useNavigate();
  const [sorting, setSorting] = useState<SortingState>([]);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [globalFilter, setGlobalFilter] = useState("");

  const columns = [
    columnHelper.display({
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
          {showIndex && <span>#</span>}
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
          {showIndex && (
            <span className="text-xs text-text-muted">
              {row.index + 1}
            </span>
          )}
        </label>
      ),
      enableSorting: false,
    }),
    columnHelper.accessor("script_text", {
      header: "Video",
      cell: ({ row }) => (
        <div className="flex items-center gap-3">
          {row.original.output_url ? (
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-content-bg">
              <Play size={14} className="text-text-secondary" />
            </div>
          ) : (
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-content-bg">
              <Film size={14} className="text-text-muted" />
            </div>
          )}
          <p
            className="max-w-xs truncate text-sm font-medium text-text-primary"
            title={row.original.script_text}
          >
            {row.original.script_text.slice(0, 60)}
            {row.original.script_text.length > 60 ? "..." : ""}
          </p>
        </div>
      ),
      enableSorting: false,
    }),
    ...(batches
      ? [
          columnHelper.accessor("batch_id", {
            header: "Batch",
            cell: (info) => {
              const batchId = info.getValue();
              if (!batchId) return <span className="text-sm text-text-muted">{"\u2014"}</span>;
              const batch = batches[batchId];
              return (
                <p className="text-sm font-medium text-text-primary">
                  {batch?.name ?? `Batch ${batchId.slice(0, 8)}`}
                </p>
              );
            },
            enableSorting: false,
          }),
        ]
      : []),
    columnHelper.accessor("status", {
      header: "Status",
      cell: (info) => (
        <StatusBadge status={info.getValue()} stage={info.row.original.current_stage} />
      ),
    }),
    columnHelper.accessor("generation_time_ms", {
      header: "Length",
      cell: (info) => {
        const val = info.getValue() ?? 0;
        return (
          <span className="text-sm text-text-secondary">
            {val > 0 ? formatDuration(val) : "\u2014"}
          </span>
        );
      },
    }),
    columnHelper.accessor("tokens_used", {
      header: "Tokens",
      cell: (info) => {
        const val = info.getValue() ?? 0;
        return (
          <span className="text-sm text-text-secondary">
            {val > 0 ? val.toLocaleString() : "\u2014"}
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
      cell: ({ row }) => <VideoActions video={row.original} onDelete={onDelete} />,
      enableSorting: false,
    }),
  ];

  const table = useReactTable({
    data: videos,
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
          .map((k) => videos[Number(k)])
          .filter((v): v is VideoRead => v !== undefined);
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
            placeholder="Search videos..."
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
                data-state={row.getIsSelected() ? "selected" : undefined}
                className="cursor-pointer border-border"
                onClick={() => {
                  navigate({
                    to: "/app/videos/$videoId",
                    params: { videoId: row.original.id },
                  });
                }}
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
    </div>
  );
}
