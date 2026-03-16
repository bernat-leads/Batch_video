import { toast } from "sonner";
import {
  downloadVideoApiV1VideosVideoIdDownloadGet,
  exportBatchZipApiV1BatchesBatchIdExportZipGet,
  exportSelectedVideosZipApiV1VideosExportZipGet,
} from "@packages/api-client";

const BLOB_OPTS = { responseType: "blob" as const };

/**
 * Creates a temporary anchor element to trigger a browser file download
 * from an in-memory blob or raw data.
 */
function triggerBrowserDownload(data: unknown, filename: string) {
  const blob = data instanceof Blob ? data : new Blob([data as BlobPart]);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/** Downloads a single video MP4 by its ID. */
export async function downloadVideo(videoId: string) {
  try {
    const data = await downloadVideoApiV1VideosVideoIdDownloadGet(videoId, BLOB_OPTS);
    triggerBrowserDownload(data, `video-${videoId.slice(0, 8)}.mp4`);
  } catch {
    toast.error("Failed to download video");
  }
}

/** Exports all videos in a batch as a ZIP file. */
export async function exportBatchZip(batchId: string, batchName: string) {
  try {
    const data = await exportBatchZipApiV1BatchesBatchIdExportZipGet(batchId, BLOB_OPTS);
    triggerBrowserDownload(data, `${batchName}.zip`);
  } catch {
    toast.error("Failed to export batch");
  }
}

/** Exports a selection of videos as a ZIP file. */
export async function exportSelectedVideosZip(videoIds: string[]) {
  try {
    const data = await exportSelectedVideosZipApiV1VideosExportZipGet(
      { video_id: videoIds },
      BLOB_OPTS,
    );
    triggerBrowserDownload(data, "videos.zip");
  } catch {
    toast.error("Failed to export videos");
  }
}
