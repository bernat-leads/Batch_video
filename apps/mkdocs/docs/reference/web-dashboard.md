# Web Dashboard — UI SOP

> Standard operating procedures for building dashboard UI. All examples use Tailwind classes — never inline styles.

---

## Route Structure

```
/                    → redirect to /app or /login
/login               → password login
/app                 → authenticated layout (sidebar + content)
/app/                → dashboard (stats, charts, recent tables)
/app/settings        → master prompt + retention config
/app/batches         → batch list with table
/app/batches/$batchId → batch detail with videos
/app/videos          → all videos list
/app/videos/$videoId → video detail (status, stats, preview, script)
```

## Auth Pattern

Route guard in `app.tsx` — calls `meApiV1AuthMeGet()` before rendering:
```tsx
export const Route = createFileRoute("/app")({
  beforeLoad: async () => {
    try { await meApiV1AuthMeGet(); }
    catch { throw redirect({ to: "/login" }); }
  },
  component: AuthenticatedLayout,
});
```

Login page has inverse guard — redirect to `/app` if already authenticated.

**No auth logic in QueryClient.** Auth is route-guard only.

---

## Layout Architecture

### Root (`__root.tsx`)
`<Outlet />` + `<Toaster position="bottom-right" richColors />` + devtools

### Authenticated (`app.tsx`)
```tsx
<SidebarProvider defaultOpen={!isSmallScreen}>
  <AppSidebar />
  <SidebarInset className="bg-content-bg">
    <div className="mx-auto w-full max-w-5xl px-8 py-8">
      <AnimatedOutlet><Outlet /></AnimatedOutlet>
    </div>
  </SidebarInset>
</SidebarProvider>
```

Content constrained to `max-w-5xl` (1024px). Route transitions via Framer Motion (no CSS View Transitions).

---

## Styling — Tailwind Theme Tokens

All colors are CSS custom properties in `global.css` `@theme` block, available as Tailwind classes.

### Color Map

| Element | Tailwind Class |
|---------|---------------|
| Page background | `bg-content-bg` |
| Card background | `bg-card-bg` |
| Card/input border | `border-border` |
| Primary text | `text-text-primary` |
| Secondary text | `text-text-secondary` |
| Muted text | `text-text-muted` |
| Brand accent | `bg-brand` / `text-brand` |
| Skeleton background | `bg-border` |
| Success | `text-status-success` / `bg-status-success-light` |
| Error | `text-status-error` / `bg-status-error-light` |
| Info | `text-status-info` / `bg-status-info-light` |

### Sidebar Theme

Mapped via CSS rule in `global.css` (not inline styles):
```css
[data-sidebar="sidebar"] {
  --sidebar: var(--sidebar-bg);
  --sidebar-foreground: var(--sidebar-text);
  --sidebar-accent: var(--sidebar-hover);
  --sidebar-accent-foreground: var(--text-primary);
  --sidebar-border: var(--sidebar-border);
}
```

---

## UI Patterns

### Card
```tsx
<div className="rounded-xl border border-border bg-card-bg p-6">
```

### Primary Button
```tsx
<Button className="bg-brand text-white hover:opacity-90">Save</Button>
```

### Outline Button
```tsx
<Button variant="outline" className="border-border text-text-secondary">Cancel</Button>
```

### Danger Button
```tsx
<Button variant="outline" className="border-border text-status-error">Delete</Button>
```

### Text Input
```tsx
<input className="h-9 w-full rounded-lg border border-border bg-content-bg px-3 text-sm text-text-primary outline-none" />
```

### Textarea
```tsx
<textarea className="min-h-[100px] w-full resize-y rounded-lg border border-border bg-content-bg px-3 py-2 text-sm text-text-primary outline-none" />
```

### Section Label
```tsx
<p className="text-xs font-medium uppercase tracking-wider text-text-muted">Section Title</p>
```

### Skeleton (Loading)
```tsx
<Skeleton className="h-28 w-full rounded-xl bg-border" />
```

### Empty State
```tsx
<EmptyState title="No videos yet" description="Create a batch to start generating videos" />
```

### Progress Bar
```tsx
<div className="h-1.5 w-full overflow-hidden rounded-full bg-border">
  <div
    className={cn("h-full rounded-full transition-all duration-500",
      failed ? "bg-status-error" : "bg-status-success")}
    style={{ width: `${percent}%` }}  {/* runtime value — exception to no-inline-style rule */}
  />
</div>
```

---

## Page Template

Every authenticated page follows this structure:

```tsx
function MyPage() {
  const { data, isLoading } = useSomeQuery();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="My Page" description="Description" />
        <Skeleton className="h-[300px] w-full rounded-xl bg-border" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="My Page" description="Description" />
      {/* Content */}
    </div>
  );
}
```

- `PageHeader` always renders (never behind loading state)
- Loading skeleton replaces only content area
- No extra wrapper — padding comes from `app.tsx` layout

---

## Status Display

### StatusBadge
```tsx
<StatusBadge status={video.status} stage={video.current_stage} />
```

| Status | Badge Style |
|--------|------------|
| pending/queued | Blue (info) |
| processing + any stage | Amber (brand) with pulse dot |
| completed | Green (success) |
| failed | Red (error) |

### Batch Status (Derived)
Batch has no `status` column. Derive it:
```tsx
import { deriveBatchStatus } from "@/lib/batch-status";
<StatusBadge status={deriveBatchStatus(batch)} />
```

### StageIndicator

Two variants:

**Compact** (default) — 6 colored bars for use in tables:
```tsx
<StageIndicator currentStage={video.current_stage} status={video.status} />
```

**Full** — icon + label pills spanning full width, for detail pages:
```tsx
<StageIndicator currentStage={video.current_stage} status={video.status} variant="full" />
```

Pipeline: `Queued → Audio (TTS) → Segmentation → Image Gen → Assembly → Done`

Each stage shows: past=green, active=brand, failed=red, future=muted.

### Delete Confirmation

All destructive actions must use `ConfirmDeleteDialog`:

```tsx
import { ConfirmDeleteDialog } from "@/components/ui/confirm-delete-dialog";

<ConfirmDeleteDialog
  title="Delete video?"
  description="This video and all its shots will be permanently deleted."
  onConfirm={() => deleteVideo.mutate({ videoId })}
>
  <Button variant="outline" size="sm" className="border-border text-status-error">
    <Trash2 size={14} className="mr-1.5" />
    Delete
  </Button>
</ConfirmDeleteDialog>
```

For dropdown menus, use `onSelect={(e) => e.preventDefault()}` on the trigger to prevent the dropdown from closing before the dialog opens.

---

## Component Inventory

### Layout (`components/layout/`)
| Component | Purpose |
|-----------|---------|
| `AppSidebar` | Collapsible sidebar nav |
| `PageHeader` | Title + description |
| `AnimatedOutlet` | Framer Motion route transitions |
| `BreadcrumbNav` | Breadcrumb with TanStack Router Links |

### Dashboard (`components/dashboard/`) — Shared
| Component | Purpose |
|-----------|---------|
| `StatusBadge` | Colored status badge |
| `StageIndicator` | Pipeline progress (compact bars or full icon pills) |
| `VideoTable` | TanStack Table for videos |
| `VideoTableSkeleton` | Loading state for video table |
| `BatchTable` | TanStack Table for batches |
| `BatchCard` | Clickable batch progress card |
| `BatchHeader` | Batch detail header with radial chart |
| `EmptyState` | Centered empty state message |
| `SelectionToolbar` | Bulk action toolbar |
| `DailyChart` | Recharts area chart for dashboard |
| `StatsCards` | Dashboard statistics cards |
| `RecentBatchesTable` | Mini table for dashboard |
| `RecentVideosTable` | Mini table for dashboard |
| `CreateBatchDialog` | Multi-step batch upload dialog |
| `CreateVideoDialog` | Multi-step single video creation |
| `FileUpload` | Drag-and-drop Excel/CSV upload |
| `ColumnMapper` | Map spreadsheet columns to fields |

### UI (`components/ui/`)
| Component | Purpose |
|-----------|---------|
| `SectionCard` | Bordered card with optional title |
| `StatRow` | Label + value row for stats |
| `Stepper` | Multi-step indicator |
| `ConfirmDeleteDialog` | Destructive action confirmation (wraps AlertDialog) |

---

## Icons & Charts

- **Icons**: `lucide-react` only. Import individually: `import { Film, Settings, Trash2 } from "lucide-react"`
- **Charts**: `recharts` only. Components: `AreaChart`, `RadialBarChart`, `Area`, `XAxis`, `YAxis`, `Tooltip`, etc.
- **NEVER create custom SVG elements** — find the closest lucide icon or recharts component

---

## Libraries

| Library | Purpose |
|---------|---------|
| `@tanstack/react-table` | Data tables (batch-table, video-table) |
| `@tanstack/react-router` | Routing |
| `@tanstack/react-query` | Data fetching (via Orval) |
| `react-hook-form` | Form state |
| `zod` | Schema validation |
| `framer-motion` | Animations |
| `sonner` | Toasts |
| `lucide-react` | Icons |
| `recharts` | Charts |
| `xlsx` | Excel/CSV parsing |
| `@packages/ui` | shadcn/ui components |
| `@packages/api-client` | Generated API hooks |
