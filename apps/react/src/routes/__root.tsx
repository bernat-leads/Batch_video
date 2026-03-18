import { createRootRoute, Outlet, useRouter } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { Toaster } from "sonner";
import { Button } from "@packages/ui/components/shadcn/button";

export const Route = createRootRoute({
  component: RootLayout,
  errorComponent: RootErrorBoundary,
});

function RootLayout() {
  return (
    <>
      <Outlet />
      <Toaster position="bottom-right" richColors />
      <TanStackRouterDevtools />
    </>
  );
}

function RootErrorBoundary({ error }: { error: Error }) {
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center bg-content-bg">
      <div className="max-w-md space-y-4 text-center">
        <h1 className="text-2xl font-semibold text-text-primary">
          Something went wrong
        </h1>
        <p className="text-sm text-text-secondary">
          {error.message || "An unexpected error occurred."}
        </p>
        <Button
          onClick={() => router.invalidate()}
          className="bg-brand text-white"
        >
          Reload
        </Button>
      </div>
    </div>
  );
}
