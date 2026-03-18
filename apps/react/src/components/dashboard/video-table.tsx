import { useNavigate } from "@tanstack/react-router";
import { createColumnHelper } from "@tanstack/react-table";
import { Download, Film, MoreHorizontal, Play } from "lucide-react";
import type { VideoRead } from "@packages/api-client";
import { videoPreviewUrl } from "@packages/api-client/urls";
import { Checkbox } from "@packages/ui/components/shadcn/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@packages/ui/components/shadcn/dropdown-menu";
import { downloadVideo } from "@/lib/download";
import { formatDate, formatDuration, formatCurrency } from "@/lib/format";
import type { PaginationInfo } from "@/lib/types";
import { DataTable } from "./data-table";
import { StatusBadge } from "./status-badge";

const col = createColumnHelper<VideoRead>();

/** Download action dropdown for a finished video. Hidden for non-finished videos. */
function VideoActions({ video }: { video: VideoRead }) {
  if (!(video.status === "finished" && video.output_url)) return null;

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
      <DropdownMenuContent align="end" className="bg-card-bg border-border">
        <DropdownMenuItem
          onClick={(e) => {
            e.stopPropagation();
            void downloadVideo(video.id);
          }}
          className="text-text-secondary"
        >
          <Download size={14} className="mr-2" />
          Download
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

interface BatchInfo {
  name: string;
}

/** Builds the column definitions for the video data table. */
function getVideoColumns(options: {
  showIndex: boolean;
  batches?: Record<string, BatchInfo>;
}) {
  return [
    col.display({
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
          {options.showIndex && <span>#</span>}
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
          {options.showIndex && (
            <span className="text-xs text-text-muted">{row.index + 1}</span>
          )}
        </label>
      ),
      enableSorting: false,
    }),
    col.display({
      id: "preview",
      header: "",
      cell: ({ row }) => (
        <div onClick={(e) => e.stopPropagation()}>
          {row.original.output_url ? (
            <a
              href={videoPreviewUrl(row.original.id)}
              target="_blank"
              rel="noopener noreferrer"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-content-bg transition-colors hover:bg-brand/10"
            >
              <Play size={14} className="text-text-secondary" />
            </a>
          ) : (
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-content-bg">
              <Film size={14} className="text-text-muted" />
            </div>
          )}
        </div>
      ),
      enableSorting: false,
    }),
    col.accessor("script_text", {
      header: "Script",
      cell: ({ row }) => (
        <p
          className="max-w-xs truncate text-sm font-medium text-text-primary"
          title={row.original.script_text}
        >
          {row.original.script_text}
        </p>
      ),
      enableSorting: false,
    }),
    // Conditionally include batch column
    ...(options.batches
      ? [
          col.accessor("batch_id", {
            header: "Batch",
            cell: (info) => {
              const batchId = info.getValue();
              if (!batchId) return <span className="text-sm text-text-muted">{"\u2014"}</span>;
              const batch = options.batches?.[batchId];
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
    col.accessor("status", {
      header: "Status",
      cell: (info) => (
        <StatusBadge status={info.getValue()} stage={info.row.original.current_stage} />
      ),
    }),
    col.accessor("duration_ms", {
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
    col.display({
      id: "cost",
      header: "Cost",
      cell: ({ row }) => {
        const val = row.original.total_cost_usd ?? 0;
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
          <VideoActions video={row.original} />
        </div>
      ),
      enableSorting: false,
    }),
  ];
}

interface VideoTableProps {
  videos: VideoRead[];
  batches?: Record<string, BatchInfo>;
  showIndex?: boolean;
  toolbar?: React.ReactNode;
  pagination?: PaginationInfo;
  onSelectionChange?: (selected: VideoRead[]) => void;
}

/**
 * Sortable, selectable data table for video listings.
 * Delegates rendering to the generic DataTable component.
 */
export function VideoTable({
  videos,
  batches,
  showIndex = true,
  toolbar,
  pagination,
  onSelectionChange,
}: VideoTableProps) {
  const navigate = useNavigate();

  return (
    <DataTable
      data={videos}
      columns={getVideoColumns({ showIndex, batches })}
      searchPlaceholder="Search videos..."
      toolbar={toolbar}
      pagination={pagination}
      onSelectionChange={onSelectionChange}
      onRowClick={(video) =>
        navigate({ to: "/app/videos/$videoId", params: { videoId: video.id } })
      }
    />
  );
}
