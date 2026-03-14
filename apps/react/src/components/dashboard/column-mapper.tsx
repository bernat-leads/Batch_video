import { useState, useMemo } from "react";
import { Button } from "@packages/ui/components/shadcn/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@packages/ui/components/shadcn/select";
import { cn } from "@packages/ui/lib/utils";

export interface ColumnMapping {
  script_text: string;
  voice_id: string;
  style: string;
  top_text: string;
}

export interface ColumnDefaults {
  script_text?: string;
  voice_id?: string;
  style?: string;
  top_text?: string;
}

interface ColumnMapperProps {
  headers: string[];
  rows: string[][];
  initialMapping?: ColumnMapping | null;
  settingsDefaults?: ColumnDefaults | null;
  onSubmit: (mapping: ColumnMapping) => void;
  onBack: () => void;
}

const UNMAPPED = "__unmapped__";

const FIELDS = [
  {
    key: "script_text" as const,
    label: "Script Text",
    description: "The ad script / video text",
    required: true,
    autoMatch: ["script_text", "script", "text", "content", "copy", "ad_text"],
  },
  {
    key: "voice_id" as const,
    label: "Voice ID",
    description: "ElevenLabs voice identifier",
    required: true,
    autoMatch: ["voice_id", "voice", "voiceid"],
  },
  {
    key: "style" as const,
    label: "Style",
    description: "Visual style (professional, energetic, etc.)",
    required: false,
    autoMatch: ["style", "visual_style", "theme"],
  },
  {
    key: "top_text" as const,
    label: "Top Text",
    description: "Text overlay at top of video",
    required: false,
    autoMatch: ["top_text", "toptext", "overlay", "banner"],
  },
] as const;

function autoDetect(headers: string[], defaults?: ColumnDefaults | null): Record<string, string> {
  const mapping: Record<string, string> = {};
  const lowerHeaders = headers.map((h) => h.toLowerCase().trim());

  for (const field of FIELDS) {
    // First check settings defaults
    const settingsDefault = defaults?.[field.key];
    if (settingsDefault) {
      const settingsLower = settingsDefault.toLowerCase().trim();
      const settingsIdx = lowerHeaders.findIndex(
        (h) => h === settingsLower || h.replace(/[\s-]/g, "_") === settingsLower,
      );
      if (settingsIdx !== -1 && headers[settingsIdx]) {
        mapping[field.key] = headers[settingsIdx];
        continue;
      }
    }

    // Fall back to built-in auto-match
    const matchIdx = lowerHeaders.findIndex((h) =>
      field.autoMatch.some((m) => h === m || h.replace(/[\s-]/g, "_") === m),
    );
    if (matchIdx !== -1 && headers[matchIdx]) {
      mapping[field.key] = headers[matchIdx];
    }
  }
  return mapping;
}

export function ColumnMapper({
  headers,
  rows,
  initialMapping,
  settingsDefaults,
  onSubmit,
  onBack,
}: ColumnMapperProps) {
  const autoMapped = useMemo(() => autoDetect(headers, settingsDefaults), [headers, settingsDefaults]);
  const [mapping, setMapping] = useState<{
    script_text: string;
    voice_id: string;
    style: string;
    top_text: string;
  }>({
    script_text: initialMapping?.script_text ?? autoMapped["script_text"] ?? UNMAPPED,
    voice_id: initialMapping?.voice_id ?? autoMapped["voice_id"] ?? UNMAPPED,
    style: initialMapping?.style ?? autoMapped["style"] ?? UNMAPPED,
    top_text: initialMapping?.top_text ?? autoMapped["top_text"] ?? UNMAPPED,
  });

  const isValid = FIELDS.filter((f) => f.required).every(
    (f) => mapping[f.key] !== UNMAPPED,
  );

  const getSamples = (columnName: string): string[] => {
    if (columnName === UNMAPPED) return [];
    const colIdx = headers.indexOf(columnName);
    if (colIdx < 0) return [];
    return rows
      .slice(0, 3)
      .map((row) => String(row[colIdx] ?? "").trim())
      .filter(Boolean);
  };

  const handleSubmit = () => {
    onSubmit(mapping);
  };

  return (
    <div className="space-y-6">
      <div className="overflow-hidden rounded-lg border border-border">
        <table className="w-full table-fixed text-sm">
          <thead>
            <tr className="bg-content-bg border-border">
              <th className="border-b border-border px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                Field
              </th>
              <th className="border-b border-border px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                Selected Column
              </th>
              <th className="border-b border-border px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                Samples
              </th>
            </tr>
          </thead>
          <tbody>
            {FIELDS.map((field, idx) => {
              const selectedValue = mapping[field.key as keyof typeof mapping];
              const samples = getSamples(selectedValue);

              return (
                <tr
                  key={field.key}
                  className={cn(
                    "border-border bg-card-bg",
                    idx < FIELDS.length - 1 && "border-b",
                  )}
                >
                  <td className="border-border px-3 py-4 align-top">
                    <p className="font-medium text-text-primary">
                      {field.label}
                      {field.required && <span className="text-status-error"> *</span>}
                    </p>
                    <p className="text-xs text-text-muted">
                      {field.description}
                    </p>
                  </td>
                  <td className="border-border px-3 py-4 align-top">
                    <Select
                      value={selectedValue}
                      onValueChange={(v) =>
                        setMapping((prev) => ({ ...prev, [field.key]: v }))
                      }
                    >
                      <SelectTrigger
                        className={cn(
                          "w-full bg-content-bg border-border",
                          selectedValue === UNMAPPED ? "text-text-muted" : "text-text-primary",
                        )}
                      >
                        <SelectValue placeholder="Select column..." />
                      </SelectTrigger>
                      <SelectContent className="bg-card-bg border-border">
                        <SelectItem value={UNMAPPED}>Select column...</SelectItem>
                        {headers.map((header) => (
                          <SelectItem key={header} value={header}>
                            {header}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </td>
                  <td className="border-border px-3 py-4 align-top">
                    {samples.length > 0 ? (
                      <div className="space-y-0.5">
                        {samples.map((s, i) => (
                          <p
                            key={i}
                            className="truncate text-xs text-text-muted"
                          >
                            {s.length > 50 ? s.slice(0, 50) + "\u2026" : s}
                          </p>
                        ))}
                      </div>
                    ) : (
                      <span className="text-xs text-border">
                        —
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-2 flex justify-between">
        <Button
          variant="outline"
          onClick={onBack}
          className="border-border text-text-secondary"
        >
          Back
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={!isValid}
          className={cn(
            isValid && "bg-brand text-white",
          )}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
