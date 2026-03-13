import { createRootRoute, Link, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { requireAuth } from "@/lib/auth";
import { LogoutButton } from "@/components/logout-button";

export const Route = createRootRoute({
  beforeLoad: ({ location }) => requireAuth(location.pathname),
  component: RootLayout,
});

function RootLayout() {
  return (
    <div className="min-h-screen bg-white text-gray-900">
      <header className="border-b border-gray-200">
        <nav className="mx-auto flex max-w-4xl items-center gap-6 px-4 py-4">
          <Link
            to="/"
            className="font-semibold text-gray-900 [&.active]:text-blue-600"
          >
            Home
          </Link>
          <Link
            to="/about"
            className="text-gray-600 hover:text-gray-900 [&.active]:text-blue-600"
          >
            About
          </Link>
          <div className="ml-auto">
            <LogoutButton />
          </div>
        </nav>
      </header>
      <main className="mx-auto max-w-4xl px-4 py-8">
        <Outlet />
      </main>
      <TanStackRouterDevtools />
    </div>
  );
}
