import { Button } from "@packages/ui/components/shadcn/button";
import { cn } from "@packages/ui/lib/utils";
import type { ColumnMapping } from "./column-mapper";
import type { ParsedFile } from "./file-upload";

interface ReviewStepProps {
  parsedFile: ParsedFile;
  mapping: ColumnMapping;
  batchName: string;
  onBatchNameChange: (name: string) => void;
  onBack: () => void;
  onConfirm: () => void;
  isSubmitting: boolean;
}

/** Step 3 of batch creation — shows batch name input and data preview table. */
export function ReviewStep({
  parsedFile,
  mapping,
  batchName,
  onBatchNameChange,
  onBack,
  onConfirm,
  isSubmitting,
}: ReviewStepProps) {
  const scriptColIdx = parsedFile.headers.indexOf(mapping.script_text);
  const totalVideos = parsedFile.rows.filter(
    (row) => scriptColIdx >= 0 && String(row[scriptColIdx]).trim() !== "",
  ).length;

  const mappedColumns = [
    { label: "Script Text", col: mapping.script_text },
    { label: "Voice ID", col: mapping.voice_id },
    { label: "Style", col: mapping.style },
    { label: "Top Text", col: mapping.top_text },
    { label: "File Name", col: mapping.file_name },
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
        <p className="text-xs text-text-muted">{parsedFile.fileName}</p>
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
                <td className="px-3 py-2 text-text-muted">{rowIdx + 1}</td>
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
