import { useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type RowSelectionState,
} from "@tanstack/react-table";

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- ColumnDef variance requires any for the value type parameter
type AnyColumnDef<T> = ColumnDef<T, any>;
import { ArrowUpDown, Search } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@packages/ui/components/shadcn/table";
import { cn } from "@packages/ui/lib/utils";
import type { PaginationInfo } from "@/lib/types";
import { TablePagination } from "./table-pagination";

interface DataTableProps<T> {
  /** Array of data items to render as rows. */
  data: T[];
  /** TanStack Table column definitions. */
  columns: AnyColumnDef<T>[];
  /** Search input placeholder text. */
  searchPlaceholder?: string;
  /** Optional toolbar rendered to the right of the search bar. */
  toolbar?: React.ReactNode;
  /** Pagination state and callbacks. Omit to hide pagination. */
  pagination?: PaginationInfo;
  /** Called with the selected items whenever row selection changes. */
  onSelectionChange?: (selected: T[]) => void;
  /** Called when a row is clicked. Receives the row data item. */
  onRowClick?: (item: T) => void;
}

/**
 * Generic sortable, filterable data table with row selection support.
 * Wraps TanStack Table with consistent search bar, header sorting indicators,
 * and pagination controls. Used by BatchTable and VideoTable.
 */
export function DataTable<T>({
  data,
  columns,
  searchPlaceholder = "Search...",
  toolbar,
  pagination,
  onSelectionChange,
  onRowClick,
}: DataTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [globalFilter, setGlobalFilter] = useState("");

  const table = useReactTable({
    data,
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
          .map((k) => data[Number(k)])
          .filter((item): item is T => item !== undefined);
        onSelectionChange(selected);
      }
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    enableRowSelection: !!onSelectionChange,
  });

  return (
    <div>
      {/* Search bar + toolbar */}
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="relative">
          <Search
            size={15}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted"
          />
          <input
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            placeholder={searchPlaceholder}
            className="h-9 w-64 rounded-lg border pl-9 pr-3 text-sm outline-none border-border bg-card-bg text-text-primary"
          />
        </div>
        {toolbar}
      </div>

      {/* Table */}
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
                    {/* Select and actions columns render their headers directly */}
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
                className={cn("border-border", onRowClick && "cursor-pointer")}
                data-state={row.getIsSelected() ? "selected" : undefined}
                onClick={() => onRowClick?.(row.original)}
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

      {/* Pagination */}
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
