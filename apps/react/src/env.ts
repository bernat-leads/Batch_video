import { createEnv } from "@t3-oss/env-core";
import { z } from "zod";
import { env as apiClientEnv } from "@packages/api-client/env";

export const env = createEnv({
  extends: [apiClientEnv],
  clientPrefix: "PUBLIC_",
  client: {
    PUBLIC_SITE_URL: z.string().url().default("http://localhost:5173"),
  },
  runtimeEnv: import.meta.env,
  // eslint-disable-next-line turbo/no-undeclared-env-vars -- build-time only, not a runtime dependency
  skipValidation: !!import.meta.env.SKIP_ENV_VALIDATION,
  emptyStringAsUndefined: true,
});
