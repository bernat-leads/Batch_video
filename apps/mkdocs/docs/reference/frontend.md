# Frontend Reference — React SOP

> Step-by-step procedures for implementing frontend features. Follow these exactly.

---

## Quick Reference

| What | Where |
|------|-------|
| App entry | `apps/react/src/main.tsx` |
| Route files | `apps/react/src/routes/` (TanStack Router, file-based) |
| Auth layout | `apps/react/src/routes/app.tsx` (sidebar + outlet) |
| Shared components | `apps/react/src/components/` |
| Route-local components | `apps/react/src/routes/<route>/_components/` |
| Hooks | `apps/react/src/hooks/` |
| Utilities | `apps/react/src/lib/` |
| Styles | `apps/react/src/styles/global.css` |
| Env config | `apps/react/src/env.ts` (t3-env) |

## Stack

| Library | Purpose |
|---------|---------|
| React 19 | UI framework |
| Vite | Build + dev server |
| TanStack Router | File-based routing, type-safe nav |
| TanStack Query | Server state (via Orval hooks) |
| React Hook Form + Zod | Form validation |
| shadcn/ui | UI primitives (`@packages/ui`) |
| Tailwind CSS v4 | Styling (via `@theme` token mapping) |
| lucide-react | Icons (ONLY icon source) |
| recharts | Charts (ONLY chart library) |
| framer-motion | Route transition animations |
| sonner | Toast notifications |
| Orval | Generated API client (`@packages/api-client`) |

---

## Project Layout

```
apps/react/src/
├── main.tsx                    # Bootstrap: QueryClientProvider + RouterProvider
├── env.ts                      # t3-env config
├── routes/
│   ├── __root.tsx              # Root: Outlet + Toaster + devtools
│   ├── index.tsx               # / → redirect to /app or /login
│   ├── login.tsx               # Login page
│   ├── app.tsx                 # Auth layout (sidebar + AnimatedOutlet)
│   └── app/
│       ├── index.tsx           # Dashboard (stats, charts, recent tables)
│       ├── settings.tsx        # Settings form (master prompt, retention)
│       ├── batches/
│       │   ├── index.tsx       # Batch list with table
│       │   ├── $batchId.tsx    # Batch detail with videos
│       │   └── _components/    # Batch-route-specific components
│       └── videos/
│           ├── index.tsx       # Video list
│           ├── $videoId.tsx    # Video detail
│           └── _components/    # Video-route-specific components
├── components/
│   ├── layout/                 # app-sidebar, page-header, animated-outlet, breadcrumb-nav
│   ├── dashboard/              # Shared: status-badge, stage-indicator, video-table, etc.
│   └── ui/                     # section-card, stat-row, stepper
├── hooks/                      # use-delete-video, use-delete-batch
├── lib/
│   ├── auth.ts                 # loginSchema only
│   ├── batch-status.ts         # deriveBatchStatus() — batch status from video counts
│   ├── format.ts               # formatDuration, formatDate, formatCurrency
│   └── query-client.ts         # Simple QueryClient export (no auth logic)
└── styles/
    └── global.css              # @theme block + base styles + sidebar overrides
```

---

## SOP: Add a New Page

1. Create route file: `src/routes/app/<name>.tsx` (or `<name>/index.tsx` for nested)
2. Export route with `createFileRoute`:
   ```tsx
   export const Route = createFileRoute("/app/<name>")(
     { component: MyPage }
   );
   ```
3. Create `_components/` folder next to the route for page-specific components
4. Use `PageHeader` for title area
5. Fetch data with Orval hooks, show `Skeleton` while loading, `EmptyState` if empty
6. Regenerate route tree: `npx @tanstack/router-cli generate`

## SOP: Add a Component

1. **Decide location:**
   - Used by one route only → `routes/<route>/_components/<name>.tsx`
   - Used by multiple routes → `components/<feature>/<name>.tsx`
   - Generic UI primitive → `components/ui/<name>.tsx`
2. One component per file, kebab-case filename
3. Export named (not default): `export function MyComponent() { ... }`
4. Style with Tailwind theme tokens — never `style={{}}`
5. Icons from `lucide-react` only — never custom SVGs

## SOP: Add a Form

1. Define Zod schema tied to Orval type:
   ```tsx
   const schema = z.object({ ... }) satisfies z.ZodType<OrvalType>;
   ```
2. Use `useForm` with `zodResolver`:
   ```tsx
   const form = useForm<OrvalType>({
     resolver: zodResolver(schema),
     defaultValues: { ... },
   });
   ```
3. Use Orval mutation with toast feedback:
   ```tsx
   const mutation = useSomeMutation({
     mutation: {
       onSuccess: () => toast.success("Done"),
       onError: () => toast.error("Failed"),
     },
   });
   ```
4. Use shadcn `Form`, `FormField`, `FormControl`, `FormItem`, `FormLabel`, `FormMessage`

## SOP: Add a Mutation with Cache Invalidation

```tsx
import { useQueryClient } from "@tanstack/react-query";
import {
  useDeleteVideoApiV1VideosVideoIdDelete,
  getListVideosApiV1VideosGetQueryKey,
} from "@packages/api-client";
import { toast } from "sonner";

const queryClient = useQueryClient();
const deleteVideo = useDeleteVideoApiV1VideosVideoIdDelete({
  mutation: {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getListVideosApiV1VideosGetQueryKey() });
      toast.success("Video deleted");
    },
    onError: () => toast.error("Failed to delete"),
  },
});
```

---

## Styling Rules

### Tailwind Theme Tokens (from `@theme` in global.css)

| Token | Class | Use For |
|-------|-------|---------|
| `--text-primary` | `text-text-primary` | Headings, primary text |
| `--text-secondary` | `text-text-secondary` | Descriptions |
| `--text-muted` | `text-text-muted` | Hints, timestamps, labels |
| `--card-bg` | `bg-card-bg` | Card backgrounds |
| `--content-bg` | `bg-content-bg` | Page/input backgrounds |
| `--border-color` | `border-border` | All borders, skeleton bg |
| `--brand` | `bg-brand` / `text-brand` | Primary buttons, accents |
| `--color-success` | `text-status-success` | Success text/dots |
| `--color-error` | `text-status-error` | Error text/dots |
| `--color-info` | `text-status-info` | Info text/dots |
| `--color-success-light` | `bg-status-success-light` | Success badge background |
| `--color-error-light` | `bg-status-error-light` | Error badge background |

### Pattern: Card

```tsx
<div className="rounded-xl border border-border bg-card-bg p-6">
```

### Pattern: Button (Primary)

```tsx
<Button className="bg-brand text-white hover:opacity-90">Save</Button>
```

### Pattern: Input

```tsx
<input className="h-9 w-full rounded-lg border border-border bg-content-bg px-3 text-sm text-text-primary outline-none" />
```

### Pattern: Skeleton

```tsx
<Skeleton className="h-28 w-full rounded-xl bg-border" />
```

---

## Auth

- Route guard in `app.tsx` `beforeLoad` → calls `meApiV1AuthMeGet()`
- If 401 → `throw redirect({ to: "/login" })`
- Login page has inverse guard (redirects to `/app` if already authed)
- **No auth logic in QueryClient** — it's a plain `new QueryClient()`

## Key Status Types

- `VideoStatus`: `pending | processing | completed | failed` (generated TS const enum)
- `VideoStage`: `queued | tts | segmentation | image_generation | assembly | upload | done`
- Batch has **no status field** — use `deriveBatchStatus(batch)` from `lib/batch-status.ts`

## Commands

| Command | Purpose |
|---------|---------|
| `pnpm dev` | Start Vite dev server |
| `pnpm build` | Production build |
| `pnpm run generate-api` | Regenerate API client |
| `npx @tanstack/router-cli generate` | Regenerate route tree |
