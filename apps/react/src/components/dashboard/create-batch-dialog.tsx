import { useState } from "react";
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
import { cn } from "@packages/ui/lib/utils";
import { Stepper } from "@/components/ui/stepper";
import { ColumnMapper, type ColumnMapping } from "./column-mapper";
import type { ColumnDefaults } from "./column-mapper";
import { FileUpload, type ParsedFile } from "./file-upload";

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

export function CreateBatchDialog({ onBatchCreated, columnDefaults }: CreateBatchDialogProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<Step>("upload");
  const [parsedFile, setParsedFile] = useState<ParsedFile | null>(null);
  const [mapping, setMapping] = useState<ColumnMapping | null>(null);
  const [batchName, setBatchName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: settings } = useGetSettingsApiV1SettingsGet();
  const uploadBatch = useUploadBatchApiV1BatchesUploadPost();

  const reset = () => {
    setStep("upload");
    setParsedFile(null);
    setMapping(null);
    setBatchName("");
    setIsSubmitting(false);
  };

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
          file: parsedFile.file,
          batch_name: finalName,
          column_mapping: JSON.stringify(mapping),
        },
      });

      queryClient.invalidateQueries({ queryKey: getListBatchesApiV1BatchesGetQueryKey() });
      queryClient.invalidateQueries({ queryKey: getListVideosApiV1VideosGetQueryKey() });
      setOpen(false);
      reset();
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
      onOpenChange={(v) => {
        setOpen(v);
        if (!v) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button className="bg-brand text-white">
          <Plus size={16} className="mr-0.5" />
          Add New
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-card-bg border-border sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-text-primary">
            Create Batch
          </DialogTitle>
          <p className="text-sm text-text-muted">
            {step === "upload" && "Upload an Excel or CSV file with your ad scripts."}
            {step === "map" && "Map your spreadsheet columns to video fields."}
            {step === "review" && "Review your batch before creating it."}
          </p>
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

function ReviewStep({
  parsedFile,
  mapping,
  batchName,
  onBatchNameChange,
  onBack,
  onConfirm,
  isSubmitting,
}: {
  parsedFile: ParsedFile;
  mapping: ColumnMapping;
  batchName: string;
  onBatchNameChange: (name: string) => void;
  onBack: () => void;
  onConfirm: () => void;
  isSubmitting: boolean;
}) {
  const scriptColIdx = parsedFile.headers.indexOf(mapping.script_text);
  const totalVideos = parsedFile.rows.filter(
    (row) => scriptColIdx >= 0 && String(row[scriptColIdx]).trim() !== "",
  ).length;

  const mappedColumns = [
    { label: "Script Text", col: mapping.script_text },
    { label: "Voice ID", col: mapping.voice_id },
    { label: "Style", col: mapping.style },
    { label: "Top Text", col: mapping.top_text },
  ];

  const colIndices = mappedColumns.map((c) => parsedFile.headers.indexOf(c.col));
  const previewRows = parsedFile.rows.slice(0, 10);

  return (
    <div className="space-y-4">
      <div>
        <label className="mb-1 block text-xs uppercase tracking-wider text-text-muted">
          Batch Name
        </label>
        <input
          value={batchName}
          onChange={(e) => onBatchNameChange(e.target.value)}
          className="h-9 w-full rounded-lg border border-border bg-content-bg px-3 text-sm font-medium text-text-primary outline-none"
        />
      </div>
      <div className="mt-1 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-text-muted">
          Preview ({Math.min(previewRows.length, 10)} of {totalVideos} videos)
        </p>
        <p className="text-xs text-text-muted">
          {parsedFile.fileName}
        </p>
      </div>
      <div className="max-h-60 overflow-auto rounded-lg border border-border">
        <table className="w-full text-xs">
          <thead className="sticky top-0">
            <tr className="bg-content-bg">
              <th className="border-b border-border px-3 py-2 text-left font-medium text-text-muted w-8">
                #
              </th>
              {mappedColumns.map((c) => (
                <th
                  key={c.label}
                  className="border-b border-border px-3 py-2 text-left font-medium text-text-muted"
                >
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {previewRows.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className={cn(
                  "bg-card-bg border-border",
                  rowIdx < previewRows.length - 1 && "border-b",
                )}
              >
                <td className="px-3 py-2 text-text-muted">
                  {rowIdx + 1}
                </td>
                {colIndices.map((colIdx, i) => {
                  const val = colIdx >= 0 ? String(row[colIdx] ?? "").trim() : "";
                  return (
                    <td
                      key={i}
                      className="max-w-[150px] truncate px-3 py-2 text-text-secondary"
                      title={val}
                    >
                      {val || "\u2014"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={onBack}
          className="border-border text-text-secondary"
          disabled={isSubmitting}
        >
          Back
        </Button>
        <Button
          onClick={onConfirm}
          className="bg-brand text-white"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Uploading..." : "Create Batch"}
        </Button>
      </div>
    </div>
  );
}
