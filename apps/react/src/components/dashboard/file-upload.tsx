import { useCallback, useRef, useState } from "react";
import { cn } from "@packages/ui/lib/utils";
import { Upload } from "lucide-react";
import * as XLSX from "xlsx";

export interface ParsedFile {
  fileName: string;
  headers: string[];
  rows: string[][];
}

interface FileUploadProps {
  onFileParsed: (data: ParsedFile) => void;
}

const ACCEPTED_TYPES = [
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.ms-excel",
  "text/csv",
];
const ACCEPTED_EXTENSIONS = ".xlsx,.xls,.csv";

export function FileUpload({ onFileParsed }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const parseFile = useCallback(
    (file: File) => {
      setError(null);
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target?.result as ArrayBuffer);
          const workbook = XLSX.read(data, { type: "array" });
          const firstSheetName = workbook.SheetNames[0];
          if (!firstSheetName) {
            setError("No sheets found in file");
            return;
          }
          const sheet = workbook.Sheets[firstSheetName];
          if (!sheet) {
            setError("No sheets found in file");
            return;
          }
          const json: string[][] = XLSX.utils.sheet_to_json(sheet!, {
            header: 1,
            defval: "",
          });
          const headerRow = json[0];
          if (!headerRow || json.length < 2) {
            setError("File must have a header row and at least one data row");
            return;
          }
          const headers = headerRow.map(String);
          const rows = json.slice(1).filter((row) => row.some((cell) => cell !== ""));
          if (rows.length === 0) {
            setError("No data rows found");
            return;
          }
          onFileParsed({ fileName: file.name, headers, rows });
        } catch {
          setError("Failed to parse file. Make sure it's a valid Excel or CSV file.");
        }
      };
      reader.readAsArrayBuffer(file);
    },
    [onFileParsed],
  );

  const handleFile = useCallback(
    (file: File) => {
      if (
        !ACCEPTED_TYPES.includes(file.type) &&
        !file.name.match(/\.(xlsx|xls|csv)$/i)
      ) {
        setError("Please upload an Excel (.xlsx, .xls) or CSV file");
        return;
      }
      parseFile(file);
    },
    [parseFile],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  return (
    <div className="space-y-3">
      <div
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 transition-colors",
          isDragging
            ? "border-brand bg-brand-muted"
            : "border-border bg-content-bg",
        )}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <div className="mb-3 text-text-muted">
          <Upload size={40} strokeWidth={1.5} />
        </div>
        <p
          className="text-sm font-medium text-text-primary"
        >
          Drop your Excel or CSV file here
        </p>
        <p className="mt-1 text-xs text-text-muted">
          or click to browse (.xlsx, .xls, .csv)
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
      </div>
      {error && (
        <p className="text-sm text-status-error">
          {error}
        </p>
      )}
    </div>
  );
}
