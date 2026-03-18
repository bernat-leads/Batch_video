import { useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus } from "lucide-react";
import {
  useUploadBatchApiV1BatchesUploadPost,
  useGetSettingsApiV1SettingsGet,
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
import { Stepper } from "@/components/ui/stepper";
import { useDialogForm } from "@/hooks/use-dialog-form";
import { ColumnMapper, type ColumnMapping } from "./column-mapper";
import type { ColumnDefaults } from "./column-mapper";
import { FileUpload, type ParsedFile } from "./file-upload";
import { ReviewStep } from "./review-step";

const DEFAULT_COLUMN_DEFAULTS: ColumnDefaults = {
  script_text: "script_text",
  voice_id: "voice_id",
  style: "style",
  top_text: "top_text",
};

interface CreateBatchDialogProps {
  onBatchCreated?: () => void;
  columnDefaults?: ColumnDefaults | null;
}

type Step = "upload" | "map" | "review";

const STEPS: { key: Step; label: string }[] = [
  { key: "upload", label: "Upload" },
  { key: "map", label: "Map Columns" },
  { key: "review", label: "Review" },
];

/** Step description shown below the dialog title. */
const STEP_DESCRIPTIONS: Record<Step, string> = {
  upload: "Upload an Excel or CSV file with your ad scripts.",
  map: "Map your spreadsheet columns to video fields.",
  review: "Review your batch before creating it.",
};

/**
 * Multi-step dialog for batch creation: Upload → Map Columns → Review.
 * Handles file parsing, column mapping, and batch upload submission.
 */
interface DialogFormState {
  step: Step;
  parsedFile: ParsedFile | null;
  mapping: ColumnMapping | null;
  batchName: string;
  isSubmitting: boolean;
}

const INITIAL_DIALOG_STATE: DialogFormState = {
  step: "upload",
  parsedFile: null,
  mapping: null,
  batchName: "",
  isSubmitting: false,
};

export function CreateBatchDialog({ onBatchCreated, columnDefaults }: CreateBatchDialogProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { open, setOpen, state, setState, onOpenChange } =
    useDialogForm<DialogFormState>(INITIAL_DIALOG_STATE);
  const { step, parsedFile, mapping, batchName, isSubmitting } = state;

  const setStep = (s: Step) => setState((prev) => ({ ...prev, step: s }));
  const setParsedFile = (f: ParsedFile | null) => setState((prev) => ({ ...prev, parsedFile: f }));
  const setMapping = (m: ColumnMapping | null) => setState((prev) => ({ ...prev, mapping: m }));
  const setBatchName = (n: string) => setState((prev) => ({ ...prev, batchName: n }));
  const setIsSubmitting = (v: boolean) => setState((prev) => ({ ...prev, isSubmitting: v }));

  const { data: settings } = useGetSettingsApiV1SettingsGet();
  const uploadBatch = useUploadBatchApiV1BatchesUploadPost();

  const handleFileParsed = (data: ParsedFile) => {
    setParsedFile(data);
    setBatchName(data.fileName.replace(/\.(xlsx|xls|csv)$/i, ""));
    setStep("map");
  };

  const handleMapped = (m: ColumnMapping) => {
    setMapping(m);
    setStep("review");
  };

  const handleConfirm = async () => {
    if (!parsedFile || !mapping || isSubmitting) return;
    setIsSubmitting(true);

    const finalName = batchName.trim() || parsedFile.fileName.replace(/\.(xlsx|xls|csv)$/i, "");

    try {
      const batch = await uploadBatch.mutateAsync({
        data: {
          // Orval types this as string but the runtime sends a File via FormData
          file: parsedFile.file as unknown as string,
          batch_name: finalName,
          column_mapping: JSON.stringify(mapping),
        },
      });

      queryClient.invalidateQueries({ queryKey: getListBatchesApiV1BatchesGetQueryKey() });
      queryClient.invalidateQueries({ queryKey: getListVideosApiV1VideosGetQueryKey() });
      onOpenChange(false);
      toast.success(`Batch "${finalName}" uploaded — processing started`);
      onBatchCreated?.();
      navigate({ to: "/app/batches/$batchId", params: { batchId: batch.id } });
    } catch {
      toast.error("Failed to upload batch");
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogTrigger asChild>
        <Button className="bg-brand text-white">
          <Plus size={16} className="mr-0.5" />
          Add New
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-card-bg border-border sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-text-primary">Create Batch</DialogTitle>
          <p className="text-sm text-text-muted">{STEP_DESCRIPTIONS[step]}</p>
          <div className="py-3">
            <Stepper steps={STEPS} current={step} />
          </div>
        </DialogHeader>

        {step === "upload" && <FileUpload onFileParsed={handleFileParsed} />}

        {step === "map" && parsedFile && (
          <ColumnMapper
            headers={parsedFile.headers}
            rows={parsedFile.rows}
            initialMapping={mapping}
            settingsDefaults={columnDefaults ?? (settings ? {
              script_text: settings.default_script_column,
              voice_id: settings.default_voice_column,
              style: settings.default_style_column,
              top_text: settings.default_top_text_column,
            } : DEFAULT_COLUMN_DEFAULTS)}
            onSubmit={handleMapped}
            onBack={() => setStep("upload")}
          />
        )}

        {step === "review" && parsedFile && mapping && (
          <ReviewStep
            parsedFile={parsedFile}
            mapping={mapping}
            batchName={batchName}
            onBatchNameChange={setBatchName}
            onBack={() => setStep("map")}
            onConfirm={handleConfirm}
            isSubmitting={isSubmitting}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
