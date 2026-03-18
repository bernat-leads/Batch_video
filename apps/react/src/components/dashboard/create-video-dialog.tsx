import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
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
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@packages/ui/components/shadcn/form";
import { cn } from "@packages/ui/lib/utils";
import { Stepper } from "@/components/ui/stepper";

type Step = "details" | "prompt";

const STEPS: { key: Step; label: string }[] = [
  { key: "details", label: "Video Details" },
  { key: "prompt", label: "Generation Prompt" },
];

interface VideoFormData {
  scriptText: string;
  voiceId: string;
  style: string;
  topText: string;
  prompt: string;
}

interface CreateVideoDialogProps {
  onVideoCreated?: () => void;
}

/**
 * Two-step dialog for creating a single video: Details → Prompt.
 * Pre-fills the generation prompt from app settings.
 */
export function CreateVideoDialog({ onVideoCreated }: CreateVideoDialogProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<Step>("details");
  const [promptInitialized, setPromptInitialized] = useState(false);

  const { data: settings } = useGetSettingsApiV1SettingsGet();

  const form = useForm<VideoFormData>({
    defaultValues: {
      scriptText: "",
      voiceId: "",
      style: "",
      topText: "",
      prompt: "",
    },
  });

  const createVideo = useCreateVideoApiV1VideosPost({
    mutation: {
      onSuccess: (data) => {
        queryClient.invalidateQueries({ queryKey: getListVideosApiV1VideosGetQueryKey() });
        queryClient.invalidateQueries({ queryKey: getListBatchesApiV1BatchesGetQueryKey() });
        setOpen(false);
        resetDialog();
        toast.success("Video created");
        onVideoCreated?.();
        navigate({ to: "/app/videos/$videoId", params: { videoId: data.id } });
      },
      onError: () => {
        toast.error("Failed to create video");
      },
    },
  });

  const resetDialog = () => {
    setStep("details");
    setPromptInitialized(false);
    form.reset();
  };

  const handleNext = () => {
    const { scriptText, voiceId } = form.getValues();
    if (!scriptText.trim() || !voiceId.trim()) return;
    if (!promptInitialized) {
      form.setValue("prompt", settings?.master_prompt ?? "");
      setPromptInitialized(true);
    }
    setStep("prompt");
  };

  const handleCreate = (values: VideoFormData) => {
    createVideo.mutate({
      data: {
        script_text: values.scriptText,
        prompt: values.prompt || settings?.master_prompt || "",
        voice_id: values.voiceId || "",
        style: values.style || undefined,
        top_text: values.topText || undefined,
      },
    });
  };

  const scriptText = form.watch("scriptText");
  const voiceId = form.watch("voiceId");
  const isNextDisabled = !scriptText.trim() || !voiceId.trim();

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        setOpen(v);
        if (!v) resetDialog();
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

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleCreate)}>
            {step === "details" && (
              <div className="space-y-4">
                <FormField
                  control={form.control}
                  name="scriptText"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-text-primary">
                        Script Text <span className="text-status-error">*</span>
                      </FormLabel>
                      <FormControl>
                        <textarea
                          placeholder="Write your video ad script..."
                          className="min-h-[100px] w-full resize-y rounded-lg border border-border bg-content-bg px-3 py-2 text-sm text-text-primary outline-none"
                          {...field}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="style"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-text-primary">
                        Style
                      </FormLabel>
                      <FormControl>
                        <textarea
                          placeholder="Additional style instructions for this video, e.g. warm golden tones, cinematic lighting, luxury brand feel..."
                          className="min-h-[60px] w-full resize-y rounded-lg border border-border bg-content-bg px-3 py-2 text-sm text-text-primary outline-none"
                          {...field}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="voiceId"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-text-primary">
                          Voice ID <span className="text-status-error">*</span>
                        </FormLabel>
                        <FormControl>
                          <input
                            placeholder="e.g. EXAVITQu4vr4xnSDxMaL"
                            className="h-9 w-full rounded-lg border border-border bg-content-bg px-3 text-sm text-text-primary outline-none"
                            {...field}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="topText"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-text-primary">
                          Top Text
                        </FormLabel>
                        <FormControl>
                          <input
                            placeholder="e.g. LIMITED OFFER"
                            className="h-9 w-full rounded-lg border border-border bg-content-bg px-3 text-sm text-text-primary outline-none"
                            {...field}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                </div>

                <div className="flex justify-end pt-1">
                  <Button
                    type="button"
                    onClick={handleNext}
                    disabled={isNextDisabled}
                    className={cn(
                      "bg-brand text-white",
                      isNextDisabled && "opacity-50",
                    )}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}

            {step === "prompt" && (
              <div className="space-y-4">
                <FormField
                  control={form.control}
                  name="prompt"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-text-primary">
                        Generation Prompt
                      </FormLabel>
                      <p className="mb-2 text-xs text-text-muted">
                        Pre-filled from your settings. Changes here apply only to this video.
                      </p>
                      <FormControl>
                        <textarea
                          placeholder="Enter generation prompt..."
                          className="min-h-[180px] w-full resize-y rounded-lg border border-border bg-content-bg px-3 py-2 text-sm text-text-primary outline-none"
                          {...field}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                <div className="flex justify-between pt-1">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setStep("details")}
                    className="border-border text-text-secondary"
                  >
                    Back
                  </Button>
                  <Button
                    type="submit"
                    className="bg-brand text-white"
                  >
                    Create Video
                  </Button>
                </div>
              </div>
            )}
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
