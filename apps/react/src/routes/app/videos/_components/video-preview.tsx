import { Film } from "lucide-react";
import { videoPreviewUrl } from "@packages/api-client/urls";

interface VideoPreviewProps {
  videoId: string;
  isFinished: boolean;
  hasOutput: boolean;
}

/** 9:16 aspect ratio video player or placeholder. Used on the video detail page. */
export function VideoPreview({ videoId, isFinished, hasOutput }: VideoPreviewProps) {
  if (isFinished && hasOutput) {
    return (
      <video
        src={videoPreviewUrl(videoId)}
        controls
        className="aspect-[9/16] w-full rounded-xl border border-border bg-black"
      />
    );
  }

  return (
    <div className="flex aspect-[9/16] items-center justify-center rounded-xl border border-border bg-content-bg">
      <Film size={32} className="text-text-muted" />
    </div>
  );
}
