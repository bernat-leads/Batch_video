import { Link, useMatchRoute, useNavigate } from "@tanstack/react-router";
import { useLogoutApiV1AuthLogoutPost } from "@packages/api-client";
import {
  LayoutDashboard,
  Layers,
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
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
  useSidebar,
} from "@packages/ui/components/shadcn/sidebar";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@packages/ui/components/shadcn/alert-dialog";

export function AppSidebar() {
  const navigate = useNavigate();
  const matchRoute = useMatchRoute();
  const { toggleSidebar, state } = useSidebar();

  const logout = useLogoutApiV1AuthLogoutPost({
    mutation: {
      onSuccess: () => navigate({ to: "/login" }),
    },
  });

  const isActive = (to: string, fuzzy = true) =>
    !!matchRoute({ to, fuzzy });

  return (
    <Sidebar
      collapsible="icon"
      className="border-r-0"
    >
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            {state === "expanded" ? (
              <div className="flex items-center justify-between overflow-hidden">
                <Link
                  to="/app"
                  className="flex items-center gap-2.5 overflow-hidden px-2 py-1.5"
                >
                  <img src="/logo.png" alt="" className="h-6 w-6 shrink-0" />
                  <span className="truncate text-lg font-semibold tracking-tight text-text-primary">
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
        <SidebarSeparator />

        {/* Video Pipeline */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-text-muted">
            Video Pipeline
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={isActive("/app", false) && !matchRoute({ to: "/app/batches", fuzzy: true }) && !matchRoute({ to: "/app/videos", fuzzy: true }) && !matchRoute({ to: "/app/settings", fuzzy: true })}
                  tooltip="Dashboard"
                >
                  <Link to="/app">
                    <LayoutDashboard size={16} />
                    <span>Dashboard</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={isActive("/app/batches")}
                  tooltip="Batches"
                >
                  <Link to="/app/batches">
                    <Layers size={16} />
                    <span>Batches</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={isActive("/app/videos")}
                  tooltip="Videos"
                >
                  <Link to="/app/videos">
                    <Film size={16} />
                    <span>Videos</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarSeparator />
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              isActive={isActive("/app/settings")}
              tooltip="Settings"
            >
              <Link to="/app/settings">
                <Settings size={16} />
                <span>Settings</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <SidebarMenuButton tooltip="Leave">
                  <LogOut size={16} />
                  <span>Leave</span>
                </SidebarMenuButton>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle className="text-text-primary">
                    Leave?
                  </AlertDialogTitle>
                  <AlertDialogDescription className="text-text-muted">
                    You will need to enter the password again to access the dashboard.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel className="border-border text-text-secondary">
                    Cancel
                  </AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => logout.mutate()}
                    className="bg-status-error text-white"
                  >
                    Leave
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
