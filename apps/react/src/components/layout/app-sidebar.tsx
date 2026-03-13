import { Link, useMatchRoute, useNavigate } from "@tanstack/react-router";
import { useLogoutApiV1AuthLogoutPost } from "@packages/api-client";
import {
  Film,
  Settings,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@packages/ui/components/shadcn/sidebar";

const NAV_ITEMS = [
  { label: "Videos", to: "/app" as const, icon: Film },
  { label: "Settings", to: "/app/settings" as const, icon: Settings },
];

export function AppSidebar() {
  const navigate = useNavigate();
  const matchRoute = useMatchRoute();
  const { toggleSidebar, state } = useSidebar();

  const logout = useLogoutApiV1AuthLogoutPost({
    mutation: {
      onSuccess: () => navigate({ to: "/login" }),
    },
  });

  return (
    <Sidebar
      collapsible="icon"
      className="border-r-0"
      style={
        {
          "--sidebar": "var(--sidebar-bg)",
          "--sidebar-foreground": "var(--sidebar-text)",
          "--sidebar-accent": "var(--sidebar-hover)",
          "--sidebar-accent-foreground": "var(--text-primary)",
          "--sidebar-border": "var(--sidebar-border)",
        } as React.CSSProperties
      }
    >
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            {state === "expanded" ? (
              <div className="flex items-center justify-between">
                <Link
                  to="/app"
                  className="flex items-center gap-2.5 px-2 py-1.5"
                >
                  <img src="/logo.png" alt="" className="h-6 w-6 shrink-0" />
                  <span
                    className="text-base font-semibold tracking-tight"
                    style={{ color: "var(--text-primary)" }}
                  >
                    Lead Alliances
                  </span>
                </Link>
                <SidebarMenuButton
                  onClick={toggleSidebar}
                  tooltip="Collapse"
                  className="h-8 w-8 shrink-0"
                >
                  <PanelLeftClose size={16} />
                </SidebarMenuButton>
              </div>
            ) : (
              <SidebarMenuButton
                onClick={toggleSidebar}
                tooltip="Expand"
              >
                <PanelLeftOpen size={16} />
              </SidebarMenuButton>
            )}
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>


      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV_ITEMS.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <SidebarMenuButton
                    asChild
                    isActive={
                      !!matchRoute({
                        to: item.to,
                        fuzzy: item.to !== "/app",
                      })
                    }
                    tooltip={item.label}
                  >
                    <Link to={item.to}>
                      <item.icon size={16} />
                      <span>{item.label}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

      </SidebarContent>


      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              onClick={() => logout.mutate()}
              tooltip="Sign out"
            >
              <LogOut size={16} />
              <span>Sign out</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
