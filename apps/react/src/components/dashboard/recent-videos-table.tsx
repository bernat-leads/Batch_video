import { Link, useNavigate } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import type { VideoRead } from "@packages/api-client";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@packages/ui/components/shadcn/table";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { formatCurrency } from "@/lib/format";

interface RecentVideosTableProps {
  videos: VideoRead[];
}

export function RecentVideosTable({ videos }: RecentVideosTableProps) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-sm font-medium text-text-primary">Recent Videos</p>
        <div className="flex items-center gap-3">
          <Link
            to="/app/videos"
            className="inline-flex items-center gap-1 text-xs text-text-muted transition-colors hover:underline"
          >
            <Plus size={12} />
            New Video
          </Link>
          <Link
            to="/app/videos"
            className="text-xs text-text-muted transition-colors hover:underline"
          >
            View all
          </Link>
        </div>
      </div>
      <div className="flex-1 overflow-hidden rounded-xl border border-border bg-card-bg">
        <Table>
          <TableHeader>
            <TableRow className="border-border bg-content-bg">
              <TableHead className="text-text-secondary">Script</TableHead>
              <TableHead className="text-text-secondary">Status</TableHead>
              <TableHead className="text-text-secondary">Cost</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {videos.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={3}
                  className="text-center text-sm text-text-muted"
                >
                  No videos yet
                </TableCell>
              </TableRow>
            ) : (
              videos.map((video) => (
                <TableRow
                  key={video.id}
                  className="cursor-pointer border-border"
                  onClick={() =>
                    navigate({
                      to: "/app/videos/$videoId",
                      params: { videoId: video.id },
                    })
                  }
                >
                  <TableCell>
                    <p
                      className="max-w-[200px] truncate text-sm font-medium text-text-primary"
                      title={video.script_text}
                    >
                      {video.script_text}
                    </p>
                  </TableCell>
                  <TableCell>
                    <StatusBadge
                      status={video.status}
                      stage={video.current_stage}
                    />
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-text-secondary">
                      {(video.total_cost_usd ?? 0) > 0
                        ? formatCurrency(video.total_cost_usd!)
                        : "\u2014"}
                    </span>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
