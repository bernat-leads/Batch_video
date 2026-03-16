import { Link, useNavigate } from "@tanstack/react-router";
import { Upload } from "lucide-react";
import type { BatchRead } from "@packages/api-client";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@packages/ui/components/shadcn/table";

interface RecentBatchesTableProps {
  batches: BatchRead[];
}

/** Compact table of the 5 most recent batches shown on the dashboard. */
export function RecentBatchesTable({ batches }: RecentBatchesTableProps) {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-sm font-medium text-text-primary">Recent Batches</p>
        <div className="flex items-center gap-3">
          <Link
            to="/app/batches"
            className="inline-flex items-center gap-1 text-xs text-text-muted transition-colors hover:underline"
          >
            <Upload size={12} />
            New Batch
          </Link>
          <Link
            to="/app/batches"
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
              <TableHead className="text-text-secondary">Name</TableHead>
              <TableHead className="text-text-secondary">Progress</TableHead>
              <TableHead className="text-text-secondary">Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {batches.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={3}
                  className="text-center text-sm text-text-muted"
                >
                  No batches yet
                </TableCell>
              </TableRow>
            ) : (
              batches.map((batch) => (
                <TableRow
                  key={batch.id}
                  className="cursor-pointer border-border"
                  onClick={() =>
                    navigate({
                      to: "/app/batches/$batchId",
                      params: { batchId: batch.id },
                    })
                  }
                >
                  <TableCell>
                    <p className="text-sm font-medium text-text-primary">
                      {batch.name}
                    </p>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-text-secondary">
                      {batch.completed_count}/{batch.total_videos} done
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-text-secondary">
                      {new Date(batch.created_at).toLocaleDateString()}
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
