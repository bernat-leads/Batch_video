import { createFileRoute } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
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

const settingsSchema = z.object({
  master_prompt: z.string(),
  retention_days: z.number().int().min(1).max(90),
  default_script_column: z.string(),
  default_voice_column: z.string(),
  default_style_column: z.string(),
  default_top_text_column: z.string(),
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

const MAPPING_FIELDS = [
  { name: "default_script_column" as const, label: "Script Text", placeholder: "e.g. script, ad_copy, text" },
  { name: "default_voice_column" as const, label: "Voice ID", placeholder: "e.g. voice_id, voice" },
  { name: "default_style_column" as const, label: "Style", placeholder: "e.g. style, video_style" },
  { name: "default_top_text_column" as const, label: "Top Text", placeholder: "e.g. top_text, headline" },
];

export const Route = createFileRoute("/app/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  const queryClient = useQueryClient();
  const { data: settings, isLoading } = useGetSettingsApiV1SettingsGet({
    query: { placeholderData: (prev) => prev },
  });

  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      master_prompt: "",
      retention_days: 7,
      default_script_column: "script_text",
      default_voice_column: "voice_id",
      default_style_column: "style",
      default_top_text_column: "top_text",
    },
    ...(settings && {
      values: {
        master_prompt: settings.master_prompt,
        retention_days: settings.retention_days,
        default_script_column: settings.default_script_column,
        default_voice_column: settings.default_voice_column,
        default_style_column: settings.default_style_column,
        default_top_text_column: settings.default_top_text_column,
      },
    }),
  });

  const updateSettings = useUpdateSettingsApiV1SettingsPut({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getGetSettingsApiV1SettingsGetQueryKey() });
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
        retention_days: values.retention_days,
        default_script_column: values.default_script_column,
        default_voice_column: values.default_voice_column,
        default_style_column: values.default_style_column,
        default_top_text_column: values.default_top_text_column,
      },
    });
  }

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Configure your video pipeline defaults"
      />

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-48 w-full rounded-xl bg-border" />
          <Skeleton className="h-32 w-full rounded-xl bg-border" />
        </div>
      ) : (
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
                    {MAPPING_FIELDS.map((mf, i) => (
                      <FormField
                        key={mf.name}
                        control={form.control}
                        name={mf.name}
                        render={({ field }) => (
                          <tr
                            className={cn(
                              i < MAPPING_FIELDS.length - 1 && "border-b border-border"
                            )}
                          >
                            <td className="px-4 py-2.5 font-medium text-text-primary">
                              {mf.label}
                            </td>
                            <td className="px-4 py-2.5">
                              <input
                                placeholder={mf.placeholder}
                                className="h-8 w-full rounded-md border border-border bg-content-bg px-2.5 text-sm text-text-primary outline-none"
                                {...field}
                              />
                            </td>
                          </tr>
                        )}
                      />
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
                      onValueChange={(val) => field.onChange(Number(val))}
                      value={String(field.value)}
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
      )}
    </div>
  );
}
