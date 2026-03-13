import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query";
import { isUnauthorized } from "@/lib/auth";

interface RouterRef {
  navigate: (opts: { to: string }) => void;
  getLocation: () => { pathname: string };
}

export function createQueryClient(router: RouterRef) {
  function handleAuthError(error: unknown) {
    if (
      isUnauthorized(error) &&
      router.getLocation().pathname !== "/login"
    ) {
      router.navigate({ to: "/login" });
    }
  }

  return new QueryClient({
    queryCache: new QueryCache({ onError: handleAuthError }),
    mutationCache: new MutationCache({ onError: handleAuthError }),
    defaultOptions: {
      queries: {
        retry: (failureCount, error) => {
          if (isUnauthorized(error)) return false;
          return failureCount < 3;
        },
      },
    },
  });
}
