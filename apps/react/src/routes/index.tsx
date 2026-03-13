import { createFileRoute, isRedirect, redirect } from "@tanstack/react-router";
import { meApiV1AuthMeGet } from "@packages/api-client";

export const Route = createFileRoute("/")({
  beforeLoad: async () => {
    try {
      await meApiV1AuthMeGet();
      throw redirect({ to: "/app" });
    } catch (e) {
      if (isRedirect(e)) throw e;
      throw redirect({ to: "/login" });
    }
  },
});
