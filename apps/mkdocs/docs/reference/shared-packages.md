# Shared Packages Reference

> How to use and extend the shared packages in this monorepo.

---

## @packages/ui — Design System

**Location:** `packages/ui/`
**Tech:** shadcn/ui (Radix UI + Tailwind CSS)

**Import pattern:**
```tsx
import { Button } from "@packages/ui/components/shadcn/button";
import { Dialog, DialogContent } from "@packages/ui/components/shadcn/dialog";
import { cn } from "@packages/ui/lib/utils";
```

**Key exports:**
- `./components/shadcn/*` — All shadcn components (button, card, checkbox, dialog, dropdown-menu, form, input, label, select, sidebar, skeleton, table, etc.)
- `./lib/utils` — `cn()` utility for conditional Tailwind class merging
- `./hooks/*` — `use-mobile`
- `./styles/*` — Tailwind CSS base styles

**Adding a new shadcn component:**
```bash
pnpm bump-ui  # Updates all shadcn components
```

---

## @packages/api-client — Generated API Client

**Location:** `packages/api-client/`
**Tech:** Orval (OpenAPI → TypeScript + react-query hooks)

Generated from FastAPI's OpenAPI spec. Provides:
- Typed hooks for all endpoints (`useListVideosApiV1VideosGet`, etc.)
- Query key functions for cache invalidation (`getListVideosApiV1VideosGetQueryKey`)
- TypeScript types for all schemas (`VideoRead`, `BatchCreate`, etc.)
- Const enum objects for Python enums (`VideoStatus`, `VideoStage`)

**Regenerate after any backend API change:**
```bash
pnpm run generate-api
```

**Usage:**
```tsx
// Hooks for queries
import { useListVideosApiV1VideosGet } from "@packages/api-client";

// Types
import type { VideoRead, BatchRead } from "@packages/api-client";

// Enums (generated from Python str enums)
import { VideoStatus, VideoStage } from "@packages/api-client";

// Query keys for cache invalidation
import { getListVideosApiV1VideosGetQueryKey } from "@packages/api-client";
```

---

## @packages/analytics — PostHog

**Location:** `packages/analytics/`

Event tracking via PostHog. Manual pageview capture, session replay on errors only.

---

## @packages/sentry — Error Tracking

**Location:** `packages/sentry/`

Shared Sentry initialization for both frontend and backend.

---

## Tooling Packages

| Package | Location | Purpose |
|---------|----------|---------|
| `@tooling/typescript-config` | `tooling/typescript-config/` | Shared tsconfig base |
| `@tooling/prettier-config` | `tooling/prettier-config/` | Import sorting + Tailwind class sorting |
| `@tooling/eslint-config` | `tooling/eslint-config/` | Shared ESLint rules |
