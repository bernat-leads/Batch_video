import type { VideoRead } from "@packages/api-client";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@packages/ui/components/shadcn/table";
import { StatusBadge } from "./status-badge";
import { StageIndicator } from "./stage-indicator";

interface VideoTableProps {
  videos: VideoRead[];
}

export function VideoTable({ videos }: VideoTableProps) {
  return (
    <div
      className="overflow-hidden rounded-xl border"
      style={{
        borderColor: "var(--border-color)",
        backgroundColor: "var(--card-bg)",
      }}
    >
      <Table>
        <TableHeader>
          <TableRow
            style={{
              borderColor: "var(--border-color)",
              backgroundColor: "var(--content-bg)",
            }}
          >
            <TableHead style={{ color: "var(--text-secondary)" }}>
              Script
            </TableHead>
            <TableHead style={{ color: "var(--text-secondary)" }}>
              Status
            </TableHead>
            <TableHead style={{ color: "var(--text-secondary)" }}>
              Pipeline
            </TableHead>
            <TableHead style={{ color: "var(--text-secondary)" }}>
              Preview
            </TableHead>
            <TableHead
              style={{ color: "var(--text-secondary)" }}
              className="text-right"
            >
              Actions
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {videos.map((video) => (
            <VideoRow key={video.id} video={video} />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function VideoRow({ video }: { video: VideoRead }) {
  return (
    <TableRow style={{ borderColor: "var(--border-color)" }}>
      <TableCell>
        <div className="max-w-xs">
          <p
            className="truncate text-sm font-medium"
            style={{ color: "var(--text-primary)" }}
            title={video.script_text}
          >
            {video.script_text.slice(0, 60)}
            {video.script_text.length > 60 ? "..." : ""}
          </p>
          {video.style && (
            <p
              className="mt-0.5 text-xs"
              style={{ color: "var(--text-muted)" }}
            >
              Style: {video.style}
            </p>
          )}
        </div>
      </TableCell>
      <TableCell>
        <StatusBadge status={video.status} stage={video.current_stage} />
      </TableCell>
      <TableCell>
        <StageIndicator
          currentStage={video.current_stage}
          status={video.status}
        />
      </TableCell>
      <TableCell>
        {video.status === "completed" && video.output_url ? (
          <div
            className="flex h-12 w-9 items-center justify-center overflow-hidden rounded-md border text-xs"
            style={{
              borderColor: "var(--border-color)",
              backgroundColor: "var(--content-bg)",
              color: "var(--text-muted)",
            }}
          >
            MP4
          </div>
        ) : (
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            —
          </span>
        )}
      </TableCell>
      <TableCell className="text-right">
        {video.status === "completed" && video.output_url ? (
          <a
            href={video.output_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-white transition-colors hover:opacity-90"
            style={{ backgroundColor: "var(--brand)" }}
          >
            Download
          </a>
        ) : video.status === "failed" ? (
          <span
            className="text-xs"
            style={{ color: "var(--color-error)" }}
            title={video.error_message ?? "Unknown error"}
          >
            {video.error_message
              ? video.error_message.slice(0, 40) +
                (video.error_message.length > 40 ? "..." : "")
              : "Error"}
          </span>
        ) : null}
      </TableCell>
    </TableRow>
  );
}
