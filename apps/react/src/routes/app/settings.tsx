import { createFileRoute } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  useGetSettingsApiV1SettingsGet,
  useUpdateSettingsApiV1SettingsPut,
} from "@packages/api-client";
import { Button } from "@packages/ui/components/shadcn/button";
import { Textarea } from "@packages/ui/components/shadcn/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@packages/ui/components/shadcn/select";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@packages/ui/components/shadcn/form";
import { Skeleton } from "@packages/ui/components/shadcn/skeleton";
import { toast } from "sonner";
import { PageHeader } from "@/components/layout/page-header";

const settingsSchema = z.object({
  master_prompt: z.string(),
  retention_days: z.number().int().min(1).max(90),
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

export const Route = createFileRoute("/app/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  const { data: settings, isLoading } = useGetSettingsApiV1SettingsGet();

  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsSchema),
    values: settings
      ? {
          master_prompt: settings.master_prompt,
          retention_days: settings.retention_days,
        }
      : { master_prompt: "", retention_days: 7 },
  });

  const updateSettings = useUpdateSettingsApiV1SettingsPut({
    mutation: {
      onSuccess: () => {
        toast.success("Settings saved");
      },
      onError: () => {
        toast.error("Failed to save settings");
      },
    },
  });

  function onSubmit(values: SettingsFormValues) {
    updateSettings.mutate({ data: values });
  }

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Configure your video pipeline defaults"
      />

      {isLoading ? (
        <Skeleton
          className="h-48 w-full rounded-xl"
          style={{ backgroundColor: "var(--border-color)" }}
        />
      ) : (

      <div
        className="rounded-xl border p-6"
        style={{
          backgroundColor: "var(--card-bg)",
          borderColor: "var(--border-color)",
        }}
      >
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="space-y-6"
          >
            <FormField
              control={form.control}
              name="master_prompt"
              render={({ field }) => (
                <FormItem>
                  <FormLabel style={{ color: "var(--text-primary)" }}>
                    Master Prompt
                  </FormLabel>
                  <FormDescription style={{ color: "var(--text-muted)" }}>
                    This prompt is prepended to every video generation request.
                    Use it to set global style, tone, or brand guidelines.
                  </FormDescription>
                  <FormControl>
                    <Textarea
                      placeholder="e.g. Use a professional, energetic tone. Target audience: small business owners aged 25-45..."
                      className="min-h-[160px] resize-y"
                      style={{
                        backgroundColor: "#FFFFFF",
                        borderColor: "var(--border-color)",
                        color: "var(--text-primary)",
                      }}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="retention_days"
              render={({ field }) => (
                <FormItem>
                  <FormLabel style={{ color: "var(--text-primary)" }}>
                    Video Retention
                  </FormLabel>
                  <FormDescription style={{ color: "var(--text-muted)" }}>
                    How long to keep generated videos before automatic deletion
                    from storage.
                  </FormDescription>
                  <Select
                    onValueChange={(val) => field.onChange(Number(val))}
                    value={String(field.value)}
                  >
                    <FormControl>
                      <SelectTrigger
                        className="w-48"
                        style={{
                          backgroundColor: "#FFFFFF",
                          borderColor: "var(--border-color)",
                          color: "var(--text-primary)",
                        }}
                      >
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

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                type="submit"
                disabled={updateSettings.isPending}
                className="text-white hover:opacity-90"
                style={{ backgroundColor: "var(--brand)" }}
              >
                {updateSettings.isPending ? "Saving..." : "Save Settings"}
              </Button>
            </div>
          </form>
        </Form>
      </div>
      )}
    </div>
  );
}
