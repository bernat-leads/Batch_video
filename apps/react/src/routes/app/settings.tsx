import { createFileRoute } from "@tanstack/react-router";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  useGetSettingsApiV1SettingsGet,
  useUpdateSettingsApiV1SettingsPut,
  getGetSettingsApiV1SettingsGetQueryKey,
} from "@packages/api-client";
import { Button } from "@packages/ui/components/shadcn/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@packages/ui/components/shadcn/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@packages/ui/components/shadcn/select";
import { Skeleton } from "@packages/ui/components/shadcn/skeleton";
import { Textarea } from "@packages/ui/components/shadcn/textarea";
import { cn } from "@packages/ui/lib/utils";
import { PageHeader } from "@/components/layout/page-header";

const columnDefaultSchema = z.object({
  field: z.string(),
  column: z.string(),
});

const settingsSchema = z.object({
  master_prompt: z.string(),
  retention_days: z.string(),
  column_defaults: z.array(columnDefaultSchema),
});

type SettingsFormValues = z.infer<typeof settingsSchema>;

const RETENTION_OPTIONS = [
  { value: "3", label: "3 days" },
  { value: "7", label: "7 days" },
  { value: "14", label: "14 days" },
  { value: "30", label: "30 days" },
  { value: "60", label: "60 days" },
  { value: "90", label: "90 days" },
];

const FIELD_LABELS: Record<string, string> = {
  script_text: "Script Text",
  voice_id: "Voice ID",
  style: "Style",
  top_text: "Top Text",
  file_name: "File Name",
};

function dictToArray(dict: Record<string, string>): { field: string; column: string }[] {
  return Object.entries(dict).map(([field, column]) => ({ field, column }));
}

function arrayToDict(arr: { field: string; column: string }[]): Record<string, string> {
  return Object.fromEntries(arr.map((item) => [item.field, item.column]));
}

export const Route = createFileRoute("/app/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  const { data: settings, isLoading } = useGetSettingsApiV1SettingsGet();

  if (isLoading || !settings) {
    return (
      <div>
        <PageHeader title="Settings" description="Configure your video pipeline defaults" />
        <div className="space-y-4">
          <Skeleton className="h-48 w-full rounded-xl bg-border" />
          <Skeleton className="h-32 w-full rounded-xl bg-border" />
        </div>
      </div>
    );
  }

  return <SettingsForm settings={settings} />;
}

function SettingsForm({ settings }: { settings: { master_prompt: string; retention_days: number; column_defaults: Record<string, string> } }) {
  const queryClient = useQueryClient();

  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      master_prompt: settings.master_prompt,
      retention_days: String(settings.retention_days),
      column_defaults: dictToArray(settings.column_defaults),
    },
  });

  const { fields } = useFieldArray({
    control: form.control,
    name: "column_defaults",
  });

  const updateSettings = useUpdateSettingsApiV1SettingsPut({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: getGetSettingsApiV1SettingsGetQueryKey() });
        toast.success("Settings saved");
      },
      onError: () => {
        toast.error("Failed to save settings");
      },
    },
  });

  function onSubmit(values: SettingsFormValues) {
    updateSettings.mutate({
      data: {
        master_prompt: values.master_prompt,
        retention_days: Number(values.retention_days),
        column_defaults: arrayToDict(values.column_defaults),
      },
    });
  }

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Configure your video pipeline defaults"
      />

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="space-y-8"
          >
            {/* Master Prompt */}
            <div>
              <FormField
                control={form.control}
                name="master_prompt"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-text-primary">
                      Master Prompt
                    </FormLabel>
                    <FormDescription className="text-text-muted">
                      This prompt is prepended to every video generation request.
                      Use it to set global style, tone, or brand guidelines.
                    </FormDescription>
                    <FormControl>
                      <Textarea
                        placeholder="e.g. Use a professional, energetic tone. Target audience: small business owners aged 25-45..."
                        className="min-h-[160px] resize-y bg-card-bg border-border text-text-primary"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="h-px bg-border" />

            {/* Default Column Mapping */}
            <div>
              <p className="text-sm font-medium text-text-primary">
                Default Column Mapping
              </p>
              <p className="mb-3 mt-1 text-sm text-text-muted">
                Default column names to auto-match when uploading spreadsheets.
              </p>
              <div className="overflow-hidden rounded-xl border border-border bg-card-bg">
                <table className="w-full table-fixed text-sm">
                  <thead>
                    <tr className="bg-content-bg">
                      <th className="border-b border-border px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                        Field
                      </th>
                      <th className="border-b border-border px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                        Default Column Name
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {fields.map((item, i) => (
                      <tr
                        key={item.id}
                        className={cn(
                          i < fields.length - 1 && "border-b border-border"
                        )}
                      >
                        <td className="px-4 py-2.5 font-medium text-text-primary">
                          {FIELD_LABELS[item.field] ?? item.field}
                        </td>
                        <td className="px-4 py-2.5">
                          <input
                            {...form.register(`column_defaults.${i}.column`)}
                            className="h-8 w-full rounded-md border border-border bg-content-bg px-2.5 text-sm text-text-primary outline-none"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="h-px bg-border" />

            {/* Storage */}
            <div>
              <FormField
                control={form.control}
                name="retention_days"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-text-primary">
                      Video Retention
                    </FormLabel>
                    <FormDescription className="text-text-muted">
                      How long to keep generated videos before automatic deletion
                      from storage.
                    </FormDescription>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger className="w-48 bg-card-bg border-border text-text-primary">
                          <SelectValue placeholder="Select duration" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {RETENTION_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                type="submit"
                disabled={updateSettings.isPending}
                className="bg-brand text-white hover:opacity-90"
              >
                {updateSettings.isPending ? "Saving..." : "Save Settings"}
              </Button>
            </div>
          </form>
        </Form>
    </div>
  );
}
