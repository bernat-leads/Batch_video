# Frontend Reference — React + Vite

## Quick Navigation

| Area | Path |
|------|------|
| App entry | `apps/react/src/main.tsx` |
| Route tree | `apps/react/src/routes/` (TanStack Router, file-based) |
| Root layout | `apps/react/src/routes/__root.tsx` |
| Components | `apps/react/src/components/` |
| Auth utilities | `apps/react/src/lib/auth.ts` |
| QueryClient factory | `apps/react/src/lib/query-client.ts` |
| Environment config | `apps/react/src/env.ts` (t3-env) |
| Vite config | `apps/react/vite.config.ts` |
| E2E tests | `apps/react/e2e/` (Playwright) |
| Styles | `apps/react/src/styles/global.css` |

## Tech Stack

| Library | Purpose |
|---------|---------|
| React 19 | UI framework |
| Vite | Build tool + dev server |
| TanStack Router | File-based routing with type-safe navigation |
| TanStack Query | Server state, caching, mutations (via Orval-generated hooks) |
| React Hook Form | Form state management |
| Zod | Schema validation (forms, env vars) |
| shadcn/ui | UI components (from `@packages/ui`) |
| t3-env | Type-safe environment variables |
| Tailwind CSS | Utility-first styling |

## Project Layout

```
apps/react/
├── src/
│   ├── main.tsx           # App bootstrap (router + query client)
│   ├── env.ts             # t3-env config (extends api-client env)
│   ├── routes/            # TanStack Router file-based routes
│   │   ├── __root.tsx     # Root layout + auth guard
│   │   ├── index.tsx      # Home page (/)
│   │   ├── login.tsx      # Login page (/login)
│   │   └── about.tsx      # About page (/about)
│   ├── components/        # Reusable components
│   │   └── logout-button.tsx
│   ├── lib/               # Shared utilities
│   │   ├── auth.ts        # requireAuth, isUnauthorized, loginSchema
│   │   └── query-client.ts # QueryClient factory with global 401 handling
│   └── styles/
│       └── global.css     # Tailwind base styles
├── e2e/                   # Playwright tests
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## App Bootstrap (`main.tsx`)

```typescript
const router = createRouter({ routeTree });
const queryClient = createQueryClient({
  navigate: (opts) => router.navigate(opts),
  getLocation: () => router.state.location,
});

createRoot(rootElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
```

The `createQueryClient` factory receives a `RouterRef` interface (not the full router type) to avoid generic type complexity while enabling navigation from error handlers.

## Routing

TanStack Router with file-based route generation. Routes live in `src/routes/` and are auto-discovered.

**Generate route tree after adding/removing route files:**
```bash
npx @tanstack/router-cli generate
```

### Route Guard

The root route's `beforeLoad` hook checks authentication on every navigation:

```typescript
// routes/__root.tsx
export const Route = createRootRoute({
  beforeLoad: ({ location }) => requireAuth(location.pathname),
  component: RootLayout,
});
```

See [Authentication](authentication.md) for details on `requireAuth` and expired session handling.

## Environment Variables

Uses **t3-env** (`@t3-oss/env-core`) for type-safe, Zod-validated env vars. The React app extends the api-client's env:

```typescript
// apps/react/src/env.ts
import { env as apiClientEnv } from "@packages/api-client/env";

export const env = createEnv({
  extends: [apiClientEnv],           // Inherits PUBLIC_API_URL
  clientPrefix: "PUBLIC_",
  client: {
    PUBLIC_SITE_URL: z.string().url().default("http://localhost:5173"),
  },
  runtimeEnv: import.meta.env,       // Vite's env object (NOT process.env)
  skipValidation: !!import.meta.env.SKIP_ENV_VALIDATION,
  emptyStringAsUndefined: true,
});
```

**Vite config** exposes `PUBLIC_` prefixed vars:
```typescript
// vite.config.ts
export default defineConfig({
  envPrefix: ["VITE_", "PUBLIC_"],
  // ...
});
```

!!! warning "No process.env"
    Vite does not provide `process.env` in the browser. Always use `import.meta.env` for runtime env access. The `vite/client` types must be included in `tsconfig.json`.

## Forms

React Hook Form + Zod + shadcn Form components. Orval-generated types are reused via `satisfies`:

```typescript
// Zod schema validates at runtime, satisfies ensures type compatibility
export const loginSchema = z.object({
  password: z.string().min(1, "Password is required"),
}) satisfies z.ZodType<LoginRequest>;

// In the component
const form = useForm<LoginRequest>({
  resolver: zodResolver(loginSchema),
  defaultValues: { password: "" },
});
```

shadcn form components (`Form`, `FormField`, `FormControl`, `FormItem`, `FormLabel`, `FormMessage`) wrap React Hook Form with accessible, styled inputs.

## Data Fetching

All API calls go through **Orval-generated hooks** from `@packages/api-client`. Never write raw `fetch` or `axios` calls to the backend.

```typescript
import { useLoginApiV1AuthLoginPost } from "@packages/api-client";

const login = useLoginApiV1AuthLoginPost({
  mutation: {
    onSuccess: () => navigate({ to: "/" }),
    onError: () => form.setError("password", { message: "Invalid password" }),
  },
});

login.mutate({ data: values });
```

**Regenerate after backend changes:**
```bash
pnpm run generate-api
```

## Import Conventions

```typescript
// 1. UI primitives from shared package
import { Button } from "@packages/ui/components/shadcn/button";
import { Card } from "@packages/ui/components/shadcn/card";

// 2. Generated API client (never hand-write fetch to FastAPI)
import { useLoginApiV1AuthLoginPost } from "@packages/api-client";
import type { LoginRequest } from "@packages/api-client";

// 3. App utilities via path alias
import { requireAuth } from "@/lib/auth";
import { env } from "@/env";
```

## Running

| Command | Purpose |
|---------|---------|
| `pnpm dev` | Start Vite dev server (from monorepo root) |
| `pnpm build` | Production build |
| `pnpm test:e2e` | Run Playwright tests (from `apps/react/`) |
| `pnpm test:e2e:debug` | Playwright with browser visible |
| `npx @tanstack/router-cli generate` | Regenerate route tree |
