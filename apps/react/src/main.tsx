import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { createQueryClient } from "@/lib/query-client";
import { routeTree } from "./routeTree.gen";
import "@/styles/global.css";

const router = createRouter({ routeTree });
const queryClient = createQueryClient({
  navigate: (opts) => router.navigate(opts),
  getLocation: () => router.state.location,
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const rootElement = document.getElementById("root")!;

createRoot(rootElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
