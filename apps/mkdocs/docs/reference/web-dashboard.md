# Web Dashboard (HYP-10) — Implementation Reference

> Complete reference for the web dashboard frontend — route architecture, components, theming, and key decisions.

---

## Architecture Overview

The dashboard is a **React SPA** (no SSR) built with Vite and TanStack Router. It serves as the control panel for the bulk video pipeline: users log in with a shared password, upload Excel scripts, monitor batch progress in real-time, and download finished videos.

**Key architectural choices:**

- **Route-level auth guards** via `beforeLoad` hooks (not a wrapper component)
- **File-based routing** under `/app` prefix for all authenticated pages
- **CSS custom properties** for theming (not Tailwind theme extension)
- **Orval-generated hooks** for all API communication (never raw fetch)
- **sonner** for toast notifications (not shadcn's built-in toast)
- **framer-motion** for page transitions between routes

---

## Route Structure

```
/                    → redirect to /app (authed) or /login (unauthed)
/login               → password-only login page
/app                 → authenticated layout (sidebar + content area)
/app/                → videos/batches dashboard (home)
/app/settings        → master prompt + retention config
/app/batches/$batchId → batch detail with video table
```

### Route Files

| File | Route | Purpose |
|------|-------|---------|
| `routes/__root.tsx` | — | Root layout: `<Outlet />` + `<Toaster />` + devtools |
| `routes/index.tsx` | `/` | Auth check → redirect to `/app` or `/login` |
| `routes/login.tsx` | `/login` | Login form with password field |
| `routes/app.tsx` | `/app` | Authenticated layout with sidebar |
| `routes/app/index.tsx` | `/app` | Batch list with 3s polling |
| `routes/app/settings.tsx` | `/app/settings` | Settings form (master prompt, retention) |
| `routes/app/batches/$batchId.tsx` | `/app/batches/:id` | Batch detail + video table |

### Auth Guard Pattern

Every protected route uses a `beforeLoad` hook that calls the `/auth/me` endpoint. If the call fails (401), it redirects to `/login`. This runs before any component renders.

```typescript
// routes/app.tsx
export const Route = createFileRoute("/app")({
  beforeLoad: async () => {
    try {
      await meApiV1AuthMeGet();
    } catch {
      throw redirect({ to: "/login" });
    }
  },
  component: AuthenticatedLayout,
});
```

The login page has the inverse guard — if already authenticated, redirect to `/app`:

```typescript
// routes/login.tsx
beforeLoad: async () => {
  try {
    await meApiV1AuthMeGet();
    throw redirect({ to: "/app" });
  } catch (e) {
    if (isRedirect(e)) throw e;
    // Not authenticated — stay on login
  }
},
```

### Global 401 Handling

The `QueryClient` factory (`lib/query-client.ts`) catches 401 errors from any API call and redirects to `/login`. This handles expired sessions during normal use, not just route transitions.

```typescript
function handleAuthError(error: unknown) {
  if (isUnauthorized(error) && router.getLocation().pathname !== "/login") {
    router.navigate({ to: "/login" });
  }
}
```

---

## Layout Architecture

### Root Layout (`__root.tsx`)

Minimal — just an `<Outlet />`, the global `<Toaster />` from sonner, and TanStack Router devtools. No auth, no sidebar.

### Authenticated Layout (`app.tsx`)

Wraps all `/app/*` routes with:

1. **SidebarProvider** — shadcn sidebar state management
2. **AppSidebar** — collapsible navigation sidebar
3. **SidebarInset** — main content area with `--content-bg` background
4. **AnimatedOutlet** — framer-motion page transitions

```typescript
function AuthenticatedLayout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset style={{ backgroundColor: "var(--content-bg)" }}>
        <main className="mx-auto w-full max-w-5xl px-8 py-8">
          <AnimatedOutlet><Outlet /></AnimatedOutlet>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
```

Content is constrained to `max-w-5xl` (1024px) with horizontal padding.

---

## Components

### Layout Components (`components/layout/`)

| Component | File | Purpose |
|-----------|------|---------|
| `AppSidebar` | `app-sidebar.tsx` | Collapsible sidebar with nav, branding, logout |
| `PageHeader` | `page-header.tsx` | Reusable title + description header |
| `AnimatedOutlet` | `animated-outlet.tsx` | framer-motion route transitions |

#### AppSidebar

- **Collapse mode**: `collapsible="icon"` — collapses to icon-only rail
- **Header**: Logo image + "Lead Alliances" title (expanded) or expand button (collapsed)
- **Nav items**: `Film` (Videos → `/app`), `Settings` (→ `/app/settings`)
- **Footer**: Sign out button using `useLogoutApiV1AuthLogoutPost`
- **Active state**: `useMatchRoute()` with fuzzy matching for nested routes
- **Icons**: All from `lucide-react` (Film, Settings, LogOut, PanelLeftClose, PanelLeftOpen)
- **Theme**: CSS custom properties passed as `--sidebar-*` variables

#### AnimatedOutlet

Uses `AnimatePresence` + `motion.div` for page transitions:

- Detects route depth to determine slide direction (deeper = slide up, shallower = slide down)
- 150ms duration, subtle `y: ±8px` offset + opacity fade
- Keys on `router.state.location.pathname` for proper exit animations

### Dashboard Components (`components/dashboard/`)

| Component | File | Purpose |
|-----------|------|---------|
| `BatchCard` | `batch-card.tsx` | Clickable card showing batch progress |
| `BatchHeader` | `batch-header.tsx` | Large progress display on batch detail page |
| `VideoTable` | `video-table.tsx` | Table of videos with status, pipeline, actions |
| `StatusBadge` | `status-badge.tsx` | Colored badge for video/pipeline status |
| `StageIndicator` | `stage-indicator.tsx` | 6-dot pipeline progress visualization |
| `VideoTableSkeleton` | `video-table-skeleton.tsx` | Loading placeholder for video table |
| `EmptyState` | `empty-state.tsx` | Centered empty state with icon + message |

#### Pipeline Stages (StageIndicator)

```
queued → tts → segmentation → image_generation → assembly → completed
```

Each stage is a dot connected by lines. Colors indicate:
- **Green**: completed stages
- **Brand amber**: currently processing
- **Red**: failed stage
- **Gray**: future stages

---

## Theming & Styling

### Approach: CSS Custom Properties

All colors are defined as CSS custom properties in `global.css`, not via Tailwind's theme config. Components reference these variables with inline `style` props. This was chosen for:

1. **Consistency** with shadcn/ui's variable-based theming
2. **Easy runtime changes** without rebuilding Tailwind
3. **No class name conflicts** with shadcn's default themes

### Color Palette

The design uses a **warm, earthy tone** inspired by the Lead Alliances brand.

```css
/* Sidebar */
--sidebar-bg: #E5DED5        /* Warm taupe */
--sidebar-text: #6B5D4D      /* Dark brown */
--sidebar-text-muted: #A89B8C /* Muted brown */
--sidebar-hover: #F0EBE4     /* Light cream */
--sidebar-active: #EBE5DC    /* Active highlight */
--sidebar-border: #C2B8AA    /* Warm gray */

/* Content area */
--content-bg: #FAF8F5        /* Off-white cream */
--card-bg: #FFFDF9           /* Near-white */
--border-color: #E8E0D4      /* Light taupe */

/* Text hierarchy */
--text-primary: #1A1612      /* Near-black */
--text-secondary: #4A3D30    /* Dark brown */
--text-muted: #8C7E6E        /* Medium taupe */

/* Brand */
--brand: #A87B50             /* Warm amber */
--brand-hover: #946A42       /* Darker amber */

/* Status colors (muted, earthy variants) */
--color-success: #5A8C5A / --color-success-light: #EFF5EF
--color-warning: #C4956A / --color-warning-light: #FDF6EF
--color-error: #B85C4D  / --color-error-light: #FDF0EE
--color-info: #6B8CAE   / --color-info-light: #EFF4F8
```

### Global CSS Overrides

```css
/* Full-viewport layout (no double scrollbars) */
html, body { height: 100%; overflow: hidden; }
#root { height: 100%; overflow: auto; }

/* Remove focus ring, use subtle shadow instead */
input:focus, textarea:focus, select:focus, [role="combobox"]:focus {
  outline: none !important;
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--brand) 25%, transparent) !important;
  ring: none;
}

/* Faster sidebar collapse animation (100ms vs 200ms default) */
[data-sidebar="sidebar"] { transition-duration: 100ms !important; }

/* Text fade on sidebar collapse */
[data-collapsible="icon"] [data-sidebar="menu-button"] span {
  opacity: 0; transition: opacity 100ms;
}
```

### View Transitions CSS

Native View Transitions API support for browsers that implement it:

```css
::view-transition-old(root) { animation: fade-out 120ms ease-in; }
::view-transition-new(root) { animation: fade-in 120ms ease-out; }
```

---

## Toast Notifications

**Library**: `sonner` (imported directly, not via shadcn's wrapper which depends on `next-themes`)

**Setup**: `<Toaster position="bottom-right" richColors />` in `__root.tsx`

**Usage pattern**: Toast for success/error feedback on mutations. Form field validation errors stay inline.

```typescript
// Settings page example
const updateSettings = useUpdateSettingsApiV1SettingsPut({
  mutation: {
    onSuccess: () => toast.success("Settings saved"),
    onError: () => toast.error("Failed to save settings"),
  },
});
```

**Decision**: sonner over shadcn's built-in `useToast` because:
- shadcn's `sonner.tsx` wrapper imports `next-themes` (not available in Vite apps)
- Direct `sonner` import is simpler and works without Next.js

---

## Data Fetching Patterns

### Orval-Generated Hooks

All API calls use hooks from `@packages/api-client`. The client is regenerated from FastAPI's OpenAPI spec.

```bash
pnpm run generate-api
```

### Polling

Batch list and video table use `refetchInterval` for real-time updates:

```typescript
const { data: batches } = useListBatchesApiV1VideosBatchesGet({
  query: { refetchInterval: 3000 },
});
```

### Direct API Calls in Route Guards

Route `beforeLoad` hooks call the API directly (not via hooks, since hooks need React context):

```typescript
import { meApiV1AuthMeGet } from "@packages/api-client";

// Direct call — not a hook
await meApiV1AuthMeGet();
```

---

## Form Pattern

All forms follow: **React Hook Form + Zod schema + shadcn Form components + Orval mutation**

```typescript
// 1. Zod schema (ties to Orval type)
const schema = z.object({ ... }) satisfies z.ZodType<OrvType>;

// 2. useForm with zodResolver
const form = useForm<OrvalType>({
  resolver: zodResolver(schema),
  defaultValues: { ... },
});

// 3. Orval mutation with toast feedback
const mutation = useSomeMutation({
  mutation: {
    onSuccess: () => toast.success("Done"),
    onError: () => toast.error("Failed"),
  },
});

// 4. Submit handler
function onSubmit(values: OrvalType) {
  mutation.mutate({ data: values });
}
```

---

## Libraries & Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `react` | 19 | UI framework |
| `@tanstack/react-router` | — | File-based routing, type-safe navigation |
| `@tanstack/react-query` | — | Server state, polling, cache |
| `react-hook-form` | — | Form state management |
| `zod` | — | Schema validation |
| `@hookform/resolvers` | — | Zod ↔ React Hook Form bridge |
| `framer-motion` | — | Page transition animations |
| `sonner` | — | Toast notifications |
| `lucide-react` | — | Icons (feather icon set) |
| `tailwindcss` | v4 | Utility CSS (with `@tailwindcss/vite` plugin) |
| `@packages/ui` | workspace | shadcn/ui components |
| `@packages/api-client` | workspace | Orval-generated API hooks |

---

## Public Assets

| File | Purpose |
|------|---------|
| `public/favicon.ico` | Browser tab icon (from leadalliances.com) |
| `public/logo.png` | Lead Alliances logo (sidebar header, login page) |

---

## E2E Tests

Located in `apps/react/e2e/`, using Playwright with mocked API responses.

### auth.spec.ts

- Unauthenticated redirects (`/` → `/login`, `/app` → `/login`)
- Login success → `/app` with "Videos" heading
- Login failure → "Invalid password" error
- Pending state → "Signing in..." button text
- Session expiry → redirect to `/login` on navigation and API calls
- Authenticated redirects (`/` → `/app`, `/login` → `/app`)
- Sign out → redirect to `/login`

### smoke.spec.ts

- Home page loads with "Videos" heading
- Settings page loads with "Settings" heading
- Navigation between pages works

### Mocking Strategy

Tests mock API endpoints via `page.route()`:
- `/api/v1/auth/me` → 200 (authenticated) or 401 (unauthenticated)
- `/api/v1/auth/login` → 200 or 401 based on test scenario
- `/api/v1/videos/batches` → empty array or fixture data
- `/api/v1/settings` → fixture settings object

---

## Key Decisions & Rationale

### Why `/app` prefix instead of pathless layout?

TanStack Router supports pathless layout routes (e.g., `_authenticated.tsx`), but using `/app` as a path prefix:
- Makes auth boundaries explicit in URLs
- Simplifies route matching for sidebar active states
- Avoids `_` prefix naming conventions

### Why CSS custom properties instead of Tailwind theme?

- shadcn/ui already uses CSS variables for its theming
- Custom properties allow runtime theme changes without rebuild
- Inline `style` props give precise per-component control
- Avoids fighting with shadcn's default color variables

### Why sonner directly instead of shadcn's Toaster?

shadcn's `sonner.tsx` wrapper imports `next-themes` for auto theme detection. Since this is a Vite app (not Next.js), we import `sonner` directly and configure it manually.

### Why framer-motion for transitions?

- React's native View Transitions API is experimental and limited
- framer-motion provides `AnimatePresence` for proper exit animations
- Direction-aware transitions (slide up for deeper, down for shallower) feel natural
- 150ms is fast enough to not feel sluggish

### Why polling instead of WebSockets?

- `refetchInterval: 3000` on react-query is simpler to implement
- Video generation takes minutes — 3s polling is not wasteful
- No WebSocket infrastructure needed (no Socket.IO, no Redis pub/sub)
- Automatic cleanup when component unmounts

### Why full-viewport layout with overflow on #root?

Using `html, body { height: 100%; overflow: hidden }` with `#root { overflow: auto }` prevents double scrollbars that occur when shadcn's sidebar and the page content both create scroll contexts.

---

## UI Component Styling Patterns

This section documents recurring patterns so new components stay visually consistent.

### Color Application Rules

| Element | CSS Variable | Notes |
|---------|-------------|-------|
| Page background | `--content-bg` | Set on `<SidebarInset>` and login page wrapper |
| Card/container background | `--card-bg` | All rounded containers (forms, batch cards) |
| Card/container border | `--border-color` | Also used for progress bar tracks, skeleton bg |
| Input/select/textarea background | `#FFFFFF` | Hardcoded white, not a variable |
| Primary text (headings, labels) | `--text-primary` | Near-black |
| Secondary text (descriptions) | `--text-secondary` | Dark brown |
| Muted text (hints, timestamps) | `--text-muted` | Medium taupe |
| Primary button background | `--brand` | Warm amber, always with `text-white` class |
| Primary button hover | `hover:opacity-90` class | Not `--brand-hover` — simpler |
| Disabled button | `disabled` prop | shadcn handles opacity |

### Card Pattern

All content containers follow this structure:

```tsx
<div
  className="rounded-xl border p-6"
  style={{
    backgroundColor: "var(--card-bg)",
    borderColor: "var(--border-color)",
  }}
>
  {/* content */}
</div>
```

- Border radius: `rounded-xl` (cards) or `rounded-2xl` (login card)
- Padding: `p-5` (compact cards like BatchCard) or `p-6` (form containers) or `p-10` (login card)
- Shadow on hover: `hover:shadow-md` (only on clickable cards)

### Input Field Pattern

All text inputs, textareas, and selects:

```tsx
<Input
  className="h-11"
  style={{
    backgroundColor: "#FFFFFF",
    borderColor: "var(--border-color)",
    color: "var(--text-primary)",
  }}
  {...field}
/>
```

- Height: `h-11` for inputs in forms
- Background: always `#FFFFFF` (pure white, not a variable)
- Focus style: controlled globally via CSS (subtle shadow, no ring)

### Button Pattern

Primary action buttons:

```tsx
<Button
  className="h-11 w-full text-white hover:opacity-90"
  style={{ backgroundColor: "var(--brand)" }}
  disabled={mutation.isPending}
>
  {mutation.isPending ? "Saving..." : "Save"}
</Button>
```

- Always show loading text while mutation is pending
- Full width in forms, auto width in toolbars
- `text-white` class + `--brand` background

### Loading States

Three patterns depending on context:

**Skeleton (list/grid):**
```tsx
<Skeleton
  className="h-28 w-full rounded-xl"
  style={{ backgroundColor: "var(--border-color)" }}
/>
```

**Skeleton (form content) — header always visible:**
```tsx
<PageHeader title="Settings" description="..." />
{isLoading ? <Skeleton ... /> : <FormContent />}
```

**Empty state:**
```tsx
<EmptyState
  title="No batches yet"
  description="Upload an Excel file to start generating videos"
/>
```

### Progress Bar Pattern

Used in BatchCard and BatchHeader:

```tsx
{/* Track */}
<div
  className="h-1.5 w-full overflow-hidden rounded-full"
  style={{ backgroundColor: "var(--border-color)" }}
>
  {/* Fill */}
  <div
    className="h-full rounded-full transition-all duration-500"
    style={{
      width: `${percent}%`,
      backgroundColor: failed ? "var(--color-error)" : "var(--color-success)",
    }}
  />
</div>
```

### Status Color Mapping

All pipeline/video statuses map to status color pairs:

| Status Category | Background | Text/Dot |
|----------------|-----------|----------|
| Pending/Queued | `--color-info-light` | `--color-info` |
| Processing (any stage) | `--color-warning-light` | `--brand` |
| Completed | `--color-success-light` | `--color-success` |
| Failed | `--color-error-light` | `--color-error` |

Processing statuses use `--brand` (not `--color-warning`) to match the app's accent color.

### Sidebar Theme Mapping

The sidebar maps custom properties to shadcn's sidebar variables.

**Important**: In Tailwind v4 + shadcn, the sidebar background variable is `--sidebar` (not `--sidebar-background`). The class `bg-sidebar` maps to `--color-sidebar` which maps to `--sidebar`.

```tsx
style={{
  "--sidebar": "var(--sidebar-bg)",
  "--sidebar-foreground": "var(--sidebar-text)",
  "--sidebar-accent": "var(--sidebar-hover)",
  "--sidebar-accent-foreground": "var(--text-primary)",
  "--sidebar-border": "var(--sidebar-border)",
} as React.CSSProperties}
```

### Responsive Sidebar Behavior

The sidebar is **always visible** — it never hides into a mobile drawer. On small screens (< 768px), it defaults to collapsed (icon-only rail). CSS overrides in `global.css` force `display: block/flex` on sidebar elements that shadcn would normally hide below `md:`.

### Page Layout Pattern

Every authenticated page follows:

```tsx
function SomePage() {
  const { data, isLoading } = useSomeQuery();
  return (
    <div>
      <PageHeader title="Title" description="Subtitle" />
      {isLoading ? <Skeleton /> : <Content data={data} />}
    </div>
  );
}
```

- `PageHeader` is always rendered (never behind loading state)
- Loading skeleton replaces only the content area
- Page container has no extra wrapper — `<main>` padding comes from `app.tsx` layout

### Icon Usage

All icons come from `lucide-react`:
- Size: `size={16}` in sidebar items, `size={18}` for password toggle
- No icon colors set — they inherit from parent text color
- Import individually: `import { Film, Settings } from "lucide-react"`

### Animation Patterns

**Page entrance (login):**
```tsx
<motion.div
  initial={{ opacity: 0, scale: 0.96, y: 10 }}
  animate={{ opacity: 1, scale: 1, y: 0 }}
  transition={{ duration: 0.3, ease: "easeOut" }}
>
```

**Route transitions (AnimatedOutlet):**
```tsx
initial={{ opacity: 0, y: direction * 8 }}
animate={{ opacity: 1, y: 0 }}
exit={{ opacity: 0, y: direction * -8 }}
transition={{ duration: 0.15, ease: "easeInOut" }}
```

### Logo with Circle Background

Used on login page above the card:

```tsx
<div
  className="flex h-14 w-14 items-center justify-center rounded-full"
  style={{ backgroundColor: "var(--border-color)" }}
>
  <img src="/logo.png" alt="Lead Alliances" className="h-8 w-8" />
</div>
```

### Notification Pattern

- **Success/error from mutations**: Use `toast.success()` / `toast.error()` from sonner
- **Form validation errors**: Stay inline via `<FormMessage />` (React Hook Form)
- **Auth errors**: Redirect to `/login` (handled globally by QueryClient)
- **Never**: Inline colored `<span>` for save status — always toast
