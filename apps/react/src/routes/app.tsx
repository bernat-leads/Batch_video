import { createFileRoute, redirect } from "@tanstack/react-router";
import { meApiV1AuthMeGet } from "@packages/api-client";
import {
  SidebarInset,
  SidebarProvider,
} from "@packages/ui/components/shadcn/sidebar";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { AnimatedOutlet } from "@/components/layout/animated-outlet";

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

const MOBILE_BREAKPOINT = 768;

function AuthenticatedLayout() {
  const isSmallScreen = window.innerWidth < MOBILE_BREAKPOINT;

  return (
    <SidebarProvider defaultOpen={!isSmallScreen}>
      <AppSidebar />
      <SidebarInset className="bg-content-bg">
        <div className="mx-auto w-full max-w-5xl px-8 py-8">
          <AnimatedOutlet />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
