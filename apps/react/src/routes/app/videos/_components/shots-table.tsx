import { useState } from "react";
import { Check, ImageIcon, Pencil, X } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import type { ShotRead } from "@packages/api-client";
import {
  useUpdateShotApiV1VideosVideoIdShotsShotIdPatch,
  getGetVideoApiV1VideosVideoIdGetQueryKey,
} from "@packages/api-client";
import { shotPreviewUrl } from "@packages/api-client/urls";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@packages/ui/components/shadcn/table";
import { Textarea } from "@packages/ui/components/shadcn/textarea";
import { cn } from "@packages/ui/lib/utils";
import { toast } from "sonner";
import { formatSeconds, formatCurrency, formatKenBurns } from "@/lib/format";

interface ShotsTableProps {
  shots: ShotRead[];
  videoId: string;
  videoStatus: string;
}

/** Table of individual shots within a video, with expandable rows for details. */
export function ShotsTable({ shots, videoId, videoStatus }: ShotsTableProps) {
  const [expandedShotId, setExpandedShotId] = useState<string | null>(null);
  const [editingShotId, setEditingShotId] = useState<string | null>(null);
  const [draftPrompt, setDraftPrompt] = useState("");
  const queryClient = useQueryClient();
  const sorted = [...shots].sort((a, b) => a.order - b.order);

  const isEditable = videoStatus === "failed";

  const updateShot = useUpdateShotApiV1VideosVideoIdShotsShotIdPatch({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getGetVideoApiV1VideosVideoIdGetQueryKey(videoId) });
        toast.success("Prompt updated");
        setEditingShotId(null);
      },
      onError: () => toast.error("Failed to update prompt"),
    },
  });

  const startEditing = (shot: ShotRead) => {
    setEditingShotId(shot.id);
    setDraftPrompt(shot.image_prompt);
  };

  const savePrompt = (shot: ShotRead) => {
    if (draftPrompt.trim() === shot.image_prompt) {
      setEditingShotId(null);
      return;
    }
    updateShot.mutate({
      videoId,
      shotId: shot.id,
      data: { image_prompt: draftPrompt.trim() },
    });
  };

  const cancelEditing = () => {
    setEditingShotId(null);
    setDraftPrompt("");
  };

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
                      <div className={cn(
                        "flex h-10 w-10 items-center justify-center rounded bg-content-bg",
                        isEditable && "border border-dashed border-status-error/40",
                      )}>
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
                    {editingShotId === shot.id ? (
                      <div className="space-y-2" onClick={(e) => e.stopPropagation()}>
                        <Textarea
                          value={draftPrompt}
                          onChange={(e) => setDraftPrompt(e.target.value)}
                          className="min-h-[80px] resize-y border-border bg-content-bg text-sm text-text-primary"
                          autoFocus
                        />
                        <div className="flex gap-1">
                          <button
                            onClick={() => savePrompt(shot)}
                            disabled={updateShot.isPending}
                            className="inline-flex h-7 items-center gap-1 rounded-md bg-brand px-2 text-xs font-medium text-white disabled:opacity-50"
                          >
                            <Check size={12} />
                            Save
                          </button>
                          <button
                            onClick={cancelEditing}
                            disabled={updateShot.isPending}
                            className="inline-flex h-7 items-center gap-1 rounded-md border border-border px-2 text-xs font-medium text-text-secondary disabled:opacity-50"
                          >
                            <X size={12} />
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="group flex items-start gap-1">
                        <p className={cn(
                          "text-sm text-text-secondary flex-1",
                          isExpanded ? "whitespace-pre-wrap break-words" : "truncate",
                        )}>
                          {shot.image_prompt}
                        </p>
                        {isEditable && !shot.image_url && (
                          <button
                            onClick={(e) => { e.stopPropagation(); startEditing(shot); }}
                            className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-content-bg"
                            title="Edit prompt"
                          >
                            <Pencil size={12} className="text-text-muted" />
                          </button>
                        )}
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-text-secondary align-top pt-3">
                    {formatSeconds(shot.start_time)} – {formatSeconds(shot.end_time)}
                  </TableCell>
                  <TableCell className="text-sm capitalize text-text-secondary align-top pt-3">
                    {formatKenBurns(shot.effect_config)}
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
