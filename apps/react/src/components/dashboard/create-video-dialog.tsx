import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus } from "lucide-react";
import {
  useGetSettingsApiV1SettingsGet,
  useCreateVideoApiV1VideosPost,
  getListVideosApiV1VideosGetQueryKey,
  getListBatchesApiV1BatchesGetQueryKey,
} from "@packages/api-client";
import { Button } from "@packages/ui/components/shadcn/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@packages/ui/components/shadcn/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@packages/ui/components/shadcn/select";
import { cn } from "@packages/ui/lib/utils";
import { Stepper } from "@/components/ui/stepper";

type Step = "details" | "prompt";

const STEPS: { key: Step; label: string }[] = [
  { key: "details", label: "Video Details" },
  { key: "prompt", label: "Generation Prompt" },
];

const STYLE_OPTIONS = [
  { value: "professional", label: "Professional" },
  { value: "energetic", label: "Energetic" },
  { value: "cinematic", label: "Cinematic" },
  { value: "minimal", label: "Minimal" },
];

interface CreateVideoDialogProps {
  onVideoCreated?: () => void;
}

export function CreateVideoDialog({ onVideoCreated }: CreateVideoDialogProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<Step>("details");

  const [scriptText, setScriptText] = useState("");
  const [voiceId, setVoiceId] = useState("");
  const [style, setStyle] = useState("");
  const [topText, setTopText] = useState("");
  const [prompt, setPrompt] = useState<string | null>(null);

  const { data: settings } = useGetSettingsApiV1SettingsGet();

  const createVideo = useCreateVideoApiV1VideosPost({
    mutation: {
      onSuccess: (data) => {
        queryClient.invalidateQueries({ queryKey: getListVideosApiV1VideosGetQueryKey() });
        queryClient.invalidateQueries({ queryKey: getListBatchesApiV1BatchesGetQueryKey() });
        setOpen(false);
        reset();
        toast.success("Video created");
        onVideoCreated?.();
        navigate({ to: "/app/videos/$videoId", params: { videoId: data.id } });
      },
      onError: () => {
        toast.error("Failed to create video");
      },
    },
  });

  const reset = () => {
    setStep("details");
    setScriptText("");
    setVoiceId("");
    setStyle("");
    setTopText("");
    setPrompt(null);
  };

  const handleNext = () => {
    if (!scriptText.trim() || !voiceId.trim()) return;
    if (prompt === null) {
      setPrompt(settings?.master_prompt ?? "");
    }
    setStep("prompt");
  };

  const handleCreate = () => {
    createVideo.mutate({
      data: {
        script_text: scriptText,
        prompt: prompt ?? settings?.master_prompt ?? "",
        voice_id: voiceId || undefined,
        style: style || undefined,
        top_text: topText || undefined,
      },
    });
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        setOpen(v);
        if (!v) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button className="bg-brand text-white">
          <Plus size={16} className="mr-0.5" />
          New Video
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-card-bg border-border sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-text-primary">
            Create Video
          </DialogTitle>
          <p className="text-sm text-text-muted">
            {step === "details" && "Enter the details for your video ad."}
            {step === "prompt" && "Customize the generation prompt for this video."}
          </p>
          <div className="py-3">
            <Stepper steps={STEPS} current={step} />
          </div>
        </DialogHeader>

        {step === "details" && (
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-text-primary">
                Script Text <span className="text-status-error">*</span>
              </label>
              <textarea
                value={scriptText}
                onChange={(e) => setScriptText(e.target.value)}
                placeholder="Write your video ad script..."
                className="min-h-[100px] w-full resize-y rounded-lg border border-border bg-content-bg px-3 py-2 text-sm text-text-primary outline-none"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-text-primary">
                Style
              </label>
              <Select value={style || "none"} onValueChange={(v) => setStyle(v === "none" ? "" : v)}>
                <SelectTrigger className="h-9 w-full border-border bg-content-bg text-text-primary">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  {STYLE_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-text-primary">
                  Voice ID <span className="text-status-error">*</span>
                </label>
                <input
                  value={voiceId}
                  onChange={(e) => setVoiceId(e.target.value)}
                  placeholder="e.g. EXAVITQu4vr4xnSDxMaL"
                  className="h-9 w-full rounded-lg border border-border bg-content-bg px-3 text-sm text-text-primary outline-none"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-text-primary">
                  Top Text
                </label>
                <input
                  value={topText}
                  onChange={(e) => setTopText(e.target.value)}
                  placeholder="e.g. LIMITED OFFER"
                  className="h-9 w-full rounded-lg border border-border bg-content-bg px-3 text-sm text-text-primary outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <Button
                onClick={handleNext}
                disabled={!scriptText.trim() || !voiceId.trim()}
                className={cn(
                  "bg-brand text-white",
                  (!scriptText.trim() || !voiceId.trim()) && "opacity-50",
                )}
              >
                Next
              </Button>
            </div>
          </div>
        )}

        {step === "prompt" && (
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-text-primary">
                Generation Prompt
              </label>
              <p className="mb-2 text-xs text-text-muted">
                Pre-filled from your settings. Changes here apply only to this video.
              </p>
              <textarea
                value={prompt ?? ""}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter generation prompt..."
                className="min-h-[180px] w-full resize-y rounded-lg border border-border bg-content-bg px-3 py-2 text-sm text-text-primary outline-none"
              />
            </div>

            <div className="flex justify-between pt-1">
              <Button
                variant="outline"
                onClick={() => setStep("details")}
                className="border-border text-text-secondary"
              >
                Back
              </Button>
              <Button
                onClick={handleCreate}
                className="bg-brand text-white"
              >
                Create Video
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
