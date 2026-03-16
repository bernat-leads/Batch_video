import { useState } from "react";
import { ImageIcon } from "lucide-react";
import type { ShotRead } from "@packages/api-client";
import { shotPreviewUrl } from "@packages/api-client/urls";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@packages/ui/components/shadcn/table";
import { cn } from "@packages/ui/lib/utils";
import { formatSeconds, formatCurrency, formatKenBurns } from "@/lib/format";

/** Table of individual shots within a video, with expandable rows for details. */
export function ShotsTable({ shots }: { shots: ShotRead[] }) {
  const [expandedShotId, setExpandedShotId] = useState<string | null>(null);
  const sorted = [...shots].sort((a, b) => a.order - b.order);

  return (
    <div>
      <p className="mb-2 text-sm font-medium text-text-primary">
        Shots ({shots.length})
      </p>
      {shots.length === 0 ? (
        <div className="flex items-center justify-center rounded-xl border border-border bg-card-bg py-10">
          <p className="text-sm text-text-muted">No shots generated yet</p>
        </div>
      ) : (
      <div className="overflow-hidden rounded-xl border border-border bg-card-bg">
        <Table>
          <TableHeader>
            <TableRow className="border-border bg-content-bg">
              <TableHead className="w-10 text-text-secondary">#</TableHead>
              <TableHead className="w-16 text-text-secondary">Image</TableHead>
              <TableHead className="text-text-secondary">Script</TableHead>
              <TableHead className="text-text-secondary">Prompt</TableHead>
              <TableHead className="w-28 text-text-secondary">Time</TableHead>
              <TableHead className="w-32 text-text-secondary">Burns</TableHead>
              <TableHead className="w-20 text-text-secondary">Cost</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((shot) => {
              const isExpanded = expandedShotId === shot.id;
              return (
                <TableRow
                  key={shot.id}
                  className="cursor-pointer border-border hover:bg-content-bg/50"
                  onClick={() => setExpandedShotId(isExpanded ? null : shot.id)}
                >
                  <TableCell className="text-xs text-text-muted align-top pt-3">
                    {shot.order}
                  </TableCell>
                  <TableCell className="align-top pt-3">
                    {shot.image_url ? (
                      <a
                        href={shotPreviewUrl(shot.video_id, shot.order)}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <img
                          src={shotPreviewUrl(shot.video_id, shot.order)}
                          alt={`Shot ${shot.order}`}
                          className="h-10 w-10 rounded object-cover cursor-pointer"
                        />
                      </a>
                    ) : (
                      <div className="flex h-10 w-10 items-center justify-center rounded bg-content-bg">
                        <ImageIcon size={14} className="text-text-muted" />
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="align-top pt-3 max-w-[200px]">
                    <p className={cn(
                      "text-sm text-text-primary",
                      isExpanded ? "whitespace-pre-wrap break-words" : "truncate",
                    )}>
                      {shot.text}
                    </p>
                  </TableCell>
                  <TableCell className="align-top pt-3 max-w-[280px]">
                    <p className={cn(
                      "text-sm text-text-secondary",
                      isExpanded ? "whitespace-pre-wrap break-words" : "truncate",
                    )}>
                      {shot.image_prompt}
                    </p>
                  </TableCell>
                  <TableCell className="text-sm text-text-secondary align-top pt-3">
                    {formatSeconds(shot.start_time)} – {formatSeconds(shot.end_time)}
                  </TableCell>
                  <TableCell className="text-sm capitalize text-text-secondary align-top pt-3">
                    {formatKenBurns(shot.ken_burns_config)}
                  </TableCell>
                  <TableCell className="text-sm text-text-secondary align-top pt-3">
                    {shot.cost_usd && shot.cost_usd > 0
                      ? formatCurrency(shot.cost_usd)
                      : "\u2014"}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
      )}

    </div>
  );
}
