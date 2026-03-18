import { useState } from "react";
import { AlertCircle, Film } from "lucide-react";
import { videoPreviewUrl } from "@packages/api-client/urls";

interface VideoPreviewProps {
  videoId: string;
  isFinished: boolean;
  hasOutput: boolean;
}

function Placeholder({ icon, text }: { icon?: React.ReactNode; text?: string }) {
  return (
    <div className="flex aspect-[9/16] flex-col items-center justify-center gap-2 rounded-xl border border-border bg-content-bg">
      {icon ?? <Film size={32} className="text-text-muted" />}
      {text && <p className="text-xs text-text-muted">{text}</p>}
    </div>
  );
}

/** 9:16 aspect ratio video player or placeholder. Used on the video detail page. */
export function VideoPreview({ videoId, isFinished, hasOutput }: VideoPreviewProps) {
  const [error, setError] = useState(false);

  if (!isFinished || !hasOutput) {
    return <Placeholder />;
  }

  if (error) {
    return (
      <Placeholder
        icon={<AlertCircle size={32} className="text-status-error" />}
        text="Failed to load preview"
      />
    );
  }

  return (
    <video
      src={videoPreviewUrl(videoId)}
      controls
      onError={() => setError(true)}
      className="aspect-[9/16] w-full rounded-xl border border-border bg-black"
    />
  );
}
