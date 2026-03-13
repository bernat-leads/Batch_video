# Shared Packages Reference

## @packages/ui — Design System

**Location:** `packages/ui/`
**Tech:** shadcn/ui (Radix UI + Tailwind CSS)

**Usage in apps:**
```tsx
import { Button } from "@packages/ui/components/button"
import { Card } from "@packages/ui/components/card"
```

**Adding a new component:**
```bash
pnpm bump-ui  # Updates all shadcn components
# Or manually add to packages/ui/src/components/
```

**Key exports:**
- `./components/*` — UI components (accordion, alert-dialog, avatar, button, card, checkbox, dialog, dropdown, form, input, label, menubar, modal, popover, progress, radio-group, scroll-area, select, separator, sheet, sidebar, skeleton, slider, switch, tabs, table, toast, toggle, tooltip, etc.)
- `./lib/*` — Utility functions (cn, etc.)
- `./hooks/*` — Custom React hooks (use-mobile, use-toast)
- `./providers/*` — Theme/context providers
- `./styles/*` — Tailwind CSS configuration

## @packages/analytics — PostHog Analytics

**Location:** `packages/analytics/`
**Tech:** PostHog (posthog-js)

**Key files:**
- `src/constants.ts` — Event name constants (POSTHOG_EVENTS)
- `src/config.ts` — PostHog configuration schema (Zod-validated)
- `src/client/client.tsx` — React provider component

**Event constants (`POSTHOG_EVENTS`):**
- `CHAT_CONVERSATION_STARTED` — User starts a new conversation
- `CHAT_MESSAGE_SENT` — User sends a message
- `USER_SIGNED_IN` — User logs in
- `USER_SIGNED_UP` — User registers
- `USER_SIGNED_OUT` — User logs out
- `PAGE_VIEW` (`$pageview`) — Manual pageview capture
- `WAITLIST_ENTRY_STARTED` / `WAITLIST_ENTRY_COMPLETED` — Waitlist flow

**Exports:**
- `./client` — React PostHogProvider component
- `./*` — Types, constants, config

**Privacy features:**
- Manual pageview capture (automatic disabled)
- Session replay on errors only (no session sampling)
- Scrubs sensitive headers (Authorization, Cookie)

**Usage in app:**
```tsx
import { useTrackEvent, POSTHOG_EVENTS } from "@/hooks/use-track-event"

const { trackEvent } = useTrackEvent()
trackEvent(POSTHOG_EVENTS.CHAT_MESSAGE_SENT, { thread_id })
```

## @packages/email — Email Templates

**Location:** `packages/email/`
**Tech:** React Email (JSX-to-email) + Resend

**Key files:**
- `index.ts` — Email client factory (`createEmailClient(config)` → Resend instance)
- `templates/contact.tsx` — Contact form email template

**Usage:** Email templates rendered server-side, sent via Resend

## @packages/api-client — Generated API Client

**Location:** `packages/api-client/`
**Tech:** Orval (OpenAPI → TypeScript + react-query hooks)

Generated from FastAPI's OpenAPI spec. Provides fully-typed hooks and request functions for all backend endpoints.

**Key files:**

| File | Purpose |
|------|---------|
| `src/generated.ts` | Orval-generated hooks and request functions |
| `src/model/` | Generated TypeScript types from Pydantic schemas |
| `src/custom-instance.ts` | Axios instance with `withCredentials: true` |
| `src/env.ts` | `PUBLIC_API_URL` via t3-env (used as Axios `baseURL`) |
| `src/index.ts` | Public exports |

**Axios instance:**
```typescript
// custom-instance.ts
export const AXIOS_INSTANCE = Axios.create({
  baseURL: env.PUBLIC_API_URL,
  withCredentials: true,  // Required for cross-origin cookie auth
});
```

`withCredentials: true` ensures cookies are sent with every request. No redirect logic in the transport layer — 401 handling is in the app's QueryClient.

**Environment:**
```typescript
// env.ts — uses import.meta.env only (no process.env)
export const env = createEnv({
  clientPrefix: "PUBLIC_",
  client: { PUBLIC_API_URL: z.string().url().default("http://localhost:8000") },
  runtimeEnv: import.meta.env,
});
```

**Generated auth hooks:**

| Hook / Function | Description |
|----------------|-------------|
| `useLoginApiV1AuthLoginPost` | Login mutation hook |
| `loginApiV1AuthLoginPost` | Login request function |
| `useLogoutApiV1AuthLogoutPost` | Logout mutation hook |
| `useMeApiV1AuthMeGet` | Session check query hook |
| `meApiV1AuthMeGet` | Session check request function |

**Regenerate after backend changes:**
```bash
pnpm run generate-api
```

**Usage in app:**
```tsx
import { useLoginApiV1AuthLoginPost } from "@packages/api-client";
import type { LoginRequest } from "@packages/api-client";

const login = useLoginApiV1AuthLoginPost({
  mutation: { onSuccess: () => navigate({ to: "/" }) },
});
login.mutate({ data: { password: "..." } });
```

## @packages/sentry — Sentry Configuration

**Location:** `packages/sentry/`
**Tech:** Sentry SDK

Shared Sentry initialization helpers used by both the Next.js app and the FastAPI service. Provides consistent DSN configuration and environment tagging.

**Usage:**
- Frontend: imported in `sentry.client.config.ts`, `sentry.server.config.ts`, `sentry.edge.config.ts`
- Backend: imported in `apps/fastapi/api/deps/sentry.py`

## Key App Dependencies (not packages, but important patterns)

These aren't shared packages but are critical dependencies used across the frontend app:

### @tanstack/react-form
Used for all form state management with Zod validation:
```tsx
const form = useForm({
  defaultValues: { email: "", name: "" },
  validators: { onChange: zodSchema },
  onSubmit: async ({ value }) => { /* handle */ },
});
```

### @tanstack/react-query
Used for server state, caching, and mutations. Orval generates hooks that use react-query:
```tsx
const { data, isLoading } = useGetItemsApiV1ItemsGet()
const mutation = useCreateItemApiV1ItemsPost({
  mutation: { onSuccess: () => queryClient.invalidateQueries({ queryKey: [...] }) },
})
```

---

## @tooling/typescript-config

**Location:** `packages/typescript-config/`
**Usage:** Shared tsconfig.json base. All apps extend this.

## @tooling/prettier-config

**Location:** `packages/prettier-config/`
**Plugins:** Import sorting, Tailwind CSS class sorting

## @tooling/eslint-config

**Location:** `packages/eslint-config/`
**Usage:** Shared ESLint rules for all packages
