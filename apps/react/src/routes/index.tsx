import { createFileRoute, isRedirect, redirect } from "@tanstack/react-router";
import { meApiV1AuthMeGet } from "@packages/api-client";

export const Route = createFileRoute("/")({
  beforeLoad: async () => {
    try {
      await meApiV1AuthMeGet();
      // eslint-disable-next-line @typescript-eslint/only-throw-error -- TanStack Router requires throwing redirect()
      throw redirect({ to: "/app" });
    } catch (e) {
      if (isRedirect(e)) throw e;
      // eslint-disable-next-line @typescript-eslint/only-throw-error -- TanStack Router requires throwing redirect()
      throw redirect({ to: "/login" });
    }
  },
});
