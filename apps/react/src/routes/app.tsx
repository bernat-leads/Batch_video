import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { meApiV1AuthMeGet } from "@packages/api-client";
import {
  SidebarInset,
  SidebarProvider,
} from "@packages/ui/components/shadcn/sidebar";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { useMediaQuery } from "@/hooks/use-media-query";

export const Route = createFileRoute("/app")({
  beforeLoad: async () => {
    try {
      await meApiV1AuthMeGet();
    } catch {
      // eslint-disable-next-line @typescript-eslint/only-throw-error -- TanStack Router requires throwing redirect()
      throw redirect({ to: "/login" });
    }
  },
  component: AuthenticatedLayout,
});

function AuthenticatedLayout() {
  const isDesktop = useMediaQuery("(min-width: 768px)");

  return (
    <SidebarProvider defaultOpen={isDesktop}>
      <AppSidebar />
      <SidebarInset className="bg-content-bg">
        <div className="mx-auto w-full max-w-5xl px-8 py-8">
          <Outlet />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
