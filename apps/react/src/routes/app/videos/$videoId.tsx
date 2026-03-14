import { useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  ChevronRight,
  Download,
  FileDown,
  Film,
  ImageIcon,
  Trash2,
} from "lucide-react";
import type { ShotRead } from "@packages/api-client";
import {
  useGetVideoApiV1VideosVideoIdGet,
  useGetBatchApiV1BatchesBatchIdGet,
} from "@packages/api-client";
import { Button } from "@packages/ui/components/shadcn/button";
import { Skeleton } from "@packages/ui/components/shadcn/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@packages/ui/components/shadcn/table";
import { cn } from "@packages/ui/lib/utils";
import { StageIndicator } from "@/components/dashboard/stage-indicator";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { BreadcrumbNav } from "@/components/layout/breadcrumb-nav";
import { SectionCard } from "@/components/ui/section-card";
import { StatRow } from "@/components/ui/stat-row";
import { ConfirmDeleteDialog } from "@/components/ui/confirm-delete-dialog";
import { useDeleteVideo } from "@/hooks/use-delete-video";
import { formatDuration, formatCurrency } from "@/lib/format";

export const Route = createFileRoute("/app/videos/$videoId")({
  component: VideoDetailPage,
});

function formatSeconds(s: number): string {
  const mins = Math.floor(s / 60);
  const secs = Math.floor(s % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "\u2014";
  const mb = bytes / (1024 * 1024);
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`;
}

function VideoDetailPage() {
  const { videoId } = Route.useParams();
  const navigate = useNavigate();
  const [showPrompt, setShowPrompt] = useState(false);

  const { data: video, isLoading } =
    useGetVideoApiV1VideosVideoIdGet(videoId);
  const batchId = video?.batch_id ?? "";
  const { data: batch } = useGetBatchApiV1BatchesBatchIdGet(batchId, {
    query: { enabled: !!batchId },
  });

  const deleteVideo = useDeleteVideo({
    onSuccess: () => navigate({ to: "/app/videos" }),
  });

  if (isLoading) return <VideoDetailSkeleton />;

  if (!video) {
    return (
      <div className="space-y-6">
        <p className="text-text-muted">Video not found.</p>
      </div>
    );
  }

  const batchName =
    batch?.name ?? (batchId ? `Batch ${batchId.slice(0, 8)}` : null);
  const scriptPreview =
    video.script_text.length > 50
      ? `${video.script_text.slice(0, 50)}...`
      : video.script_text;

  const breadcrumbItems =
    batchId && batchName
      ? [
          { label: "Batches", to: "/app/batches" },
          {
            label: batchName,
            to: "/app/batches/$batchId",
            params: { batchId },
          },
          { label: `Video ${videoId.slice(0, 8)}` },
        ]
      : [
          { label: "Videos", to: "/app/videos" },
          { label: `Video ${videoId.slice(0, 8)}` },
        ];

  const shots = video.shots ?? [];
  const width = video.width ?? 1080;
  const height = video.height ?? 1920;

  return (
    <div className="space-y-6">
      <BreadcrumbNav items={breadcrumbItems} />

      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-text-primary">
              Video {videoId.slice(0, 8)}
            </h1>
            <StatusBadge
              status={video.status}
              stage={video.current_stage}
            />
          </div>
          <p className="mt-1 text-sm text-text-secondary">
            {scriptPreview} — Created {new Date(video.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className="flex items-center gap-2 pt-1">
          {video.status === "completed" && video.output_url && (
            <Button
              variant="outline"
              size="sm"
              asChild
              className="border-border text-text-secondary"
            >
              <a href={video.output_url!} download>
                <FileDown size={14} className="mr-1.5" />
                Export
              </a>
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            disabled={video.status !== "completed" || !video.output_url}
            onClick={() => window.open(video.output_url!, "_blank")}
            className="border-border text-text-secondary"
          >
            <Download size={14} className="mr-1.5" />
            Download
          </Button>
          <ConfirmDeleteDialog
            title="Delete video?"
            description="This video and all its shots will be permanently deleted."
            onConfirm={() => deleteVideo.mutate({ videoId })}
          >
            <Button
              variant="outline"
              size="sm"
              className="border-border text-status-error"
            >
              <Trash2 size={14} className="mr-1.5" />
              Delete
            </Button>
          </ConfirmDeleteDialog>
        </div>
      </div>

      {video.error_message && (
        <div className="-mt-3 rounded-lg bg-status-error-light px-4 py-2">
          <p className="text-sm text-status-error">{video.error_message}</p>
        </div>
      )}

      {/* Hero: Preview + Info */}
      <div className="flex min-w-0 gap-6">
        {/* Left: Video preview */}
        <div className="w-[280px] shrink-0">
          {video.status === "completed" && video.output_url ? (
            <video
              src={video.output_url}
              controls
              className="w-full rounded-xl border border-border bg-black"
              style={{ aspectRatio: "9/16" }}
            />
          ) : (
            <div
              className="flex items-center justify-center rounded-xl border border-border bg-content-bg"
              style={{ aspectRatio: "9/16" }}
            >
              <Film size={32} className="text-text-muted" />
            </div>
          )}
        </div>

        {/* Right: Info cards */}
        <div className="flex min-w-[320px] flex-1 flex-col gap-5">
          {/* Details */}
          <div>
            <p className="mb-2 text-sm font-medium text-text-primary">
              Details
            </p>
          <SectionCard>
            <div className="space-y-2 text-sm">
              <StatRow
                label="Style"
                value={video.style ?? "\u2014"}
                valueClassName="capitalize"
              />
              <StatRow
                label="Voice ID"
                value={video.voice_id ?? "\u2014"}
                valueClassName="max-w-[120px] truncate"
              />
              <StatRow label="Top Text" value={video.top_text ?? "\u2014"} />
            </div>

            <div className="my-4 h-px bg-border" />

            <div className="space-y-2 text-sm">
              <StatRow
                label="Dimensions"
                value={`${width} \u00d7 ${height}`}
              />
              <StatRow
                label="File Size"
                value={formatFileSize(video.file_size_bytes ?? 0)}
              />
            </div>
          </SectionCard>
          </div>

          {/* Statistics */}
          <div>
            <p className="mb-2 text-sm font-medium text-text-primary">
              Statistics
            </p>
            <SectionCard>
              <div className="flex min-w-0 gap-0">
                {/* Totals column */}
                <div className="min-w-0 flex-1 space-y-2 text-sm">
                  <p className="text-xs font-medium text-text-secondary">
                    Totals
                  </p>
                  <StatRow
                    label="Video Length"
                    value={
                      video.generation_time_ms
                        ? formatDuration(video.generation_time_ms)
                        : "\u2014"
                    }
                  />
                  <StatRow
                    label="Tokens"
                    value={
                      video.tokens_used?.toLocaleString() ?? "\u2014"
                    }
                  />
                  <StatRow
                    label="Cost"
                    value={
                      video.total_cost_usd
                        ? formatCurrency(video.total_cost_usd)
                        : "\u2014"
                    }
                  />
                </div>

                {/* Separator */}
                <div className="mx-5 w-px bg-border" />

                {/* Per Shot Avg column */}
                <div className="min-w-0 flex-1 space-y-2 text-sm">
                  <p className="text-xs font-medium text-text-secondary">
                    Per Shot Avg
                  </p>
                  <StatRow
                    label="Video Length"
                    value={
                      video.avg_generation_time_per_shot_ms
                        ? formatDuration(
                            video.avg_generation_time_per_shot_ms,
                          )
                        : "\u2014"
                    }
                  />
                  <StatRow
                    label="Tokens"
                    value={
                      video.avg_tokens_per_shot
                        ? video.avg_tokens_per_shot.toLocaleString()
                        : "\u2014"
                    }
                  />
                  <StatRow
                    label="Cost"
                    value={
                      video.avg_cost_per_shot_usd
                        ? formatCurrency(video.avg_cost_per_shot_usd)
                        : "\u2014"
                    }
                  />
                </div>
              </div>
            </SectionCard>
          </div>

        </div>
      </div>

      {/* Pipeline — full width */}
      <div>
        <div className="mb-2">
          <p className="text-sm font-medium text-text-primary">Pipeline</p>
          <p className="text-xs text-text-muted">
            Audio, segmentation, image generation, and assembly stages
          </p>
        </div>
        <SectionCard>
          <StageIndicator
            currentStage={video.current_stage}
            status={video.status}
            variant="full"
          />
        </SectionCard>
      </div>

      {/* Collapsible prompt & script */}
      {(video.prompt || video.script_text) && (
        <div>
          <button
            onClick={() => setShowPrompt(!showPrompt)}
            className="flex items-center gap-2 text-sm text-text-muted transition-colors hover:text-text-secondary"
          >
            <ChevronRight
              size={14}
              className={cn(
                "transition-transform",
                showPrompt && "rotate-90",
              )}
            />
            {showPrompt ? "Hide" : "Show"} Prompt & Script
          </button>
          {showPrompt && (
            <div className="mt-3 flex gap-4">
              {video.prompt && (
                <div className="flex-1 rounded-xl border border-border bg-card-bg p-4">
                  <p className="mb-1 text-xs font-medium text-text-muted">
                    Prompt
                  </p>
                  <p className="text-sm leading-relaxed text-text-secondary">
                    {video.prompt}
                  </p>
                </div>
              )}
              <div className="flex-1 rounded-xl border border-border bg-card-bg p-4">
                <p className="mb-1 text-xs font-medium text-text-muted">
                  Script
                </p>
                <p className="text-sm leading-relaxed text-text-primary">
                  {video.script_text}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Shots table */}
      <ShotsTable shots={shots} />
    </div>
  );
}

function ShotsTable({ shots }: { shots: ShotRead[] }) {
  const [expandedShot, setExpandedShot] = useState<string | null>(null);

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
              <TableHead className="text-text-secondary">Text</TableHead>
              <TableHead className="w-28 text-text-secondary">Time</TableHead>
              <TableHead className="w-16 text-text-secondary">Image</TableHead>
              <TableHead className="w-20 text-text-secondary">
                Tokens
              </TableHead>
              <TableHead className="w-20 text-text-secondary">Cost</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((shot) => {
              const isExpanded = expandedShot === shot.id;
              return (
                <TableRow
                  key={shot.id}
                  className="cursor-pointer border-border"
                  onClick={() =>
                    setExpandedShot(isExpanded ? null : shot.id)
                  }
                >
                  <TableCell className="text-xs text-text-muted">
                    {shot.order}
                  </TableCell>
                  <TableCell>
                    <p
                      className={cn(
                        "max-w-md text-sm text-text-primary",
                        !isExpanded && "line-clamp-2",
                      )}
                    >
                      {shot.text}
                    </p>
                    {isExpanded && (
                      <div className="mt-3 space-y-2 border-t border-border pt-3">
                        <div>
                          <p className="text-xs font-medium text-text-muted">
                            Image Prompt
                          </p>
                          <p className="mt-0.5 text-xs leading-relaxed text-text-secondary">
                            {shot.image_prompt}
                          </p>
                        </div>
                        {shot.ken_burns_config && (
                          <div>
                            <p className="text-xs font-medium text-text-muted">
                              Ken Burns
                            </p>
                            <p className="mt-0.5 text-xs text-text-secondary">
                              {JSON.stringify(shot.ken_burns_config)}
                            </p>
                          </div>
                        )}
                        <div>
                          <p className="text-xs font-medium text-text-muted">
                            Model
                          </p>
                          <p className="mt-0.5 text-xs text-text-secondary">
                            Gemini Imagen 3
                          </p>
                        </div>
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-text-secondary">
                    {formatSeconds(shot.start_time)} –{" "}
                    {formatSeconds(shot.end_time)}
                  </TableCell>
                  <TableCell>
                    {shot.image_url ? (
                      <img
                        src={shot.image_url as string}
                        alt={`Shot ${shot.order}`}
                        className="h-10 w-10 rounded object-cover"
                      />
                    ) : (
                      <div className="flex h-10 w-10 items-center justify-center rounded bg-content-bg">
                        <ImageIcon size={14} className="text-text-muted" />
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-text-secondary">
                    {shot.tokens_used?.toLocaleString() ?? "\u2014"}
                  </TableCell>
                  <TableCell className="text-sm text-text-secondary">
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

function VideoDetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-6 w-64 bg-border" />
      <Skeleton className="h-16 w-full bg-border" />
      <div className="flex gap-6">
        <Skeleton className="h-[500px] w-[280px] rounded-xl bg-border" />
        <div className="flex min-w-[320px] flex-1 flex-col gap-5">
          <Skeleton className="h-[280px] rounded-xl bg-border" />
          <Skeleton className="h-[140px] rounded-xl bg-border" />
        </div>
      </div>
      <Skeleton className="h-[60px] w-full rounded-xl bg-border" />
    </div>
  );
}
