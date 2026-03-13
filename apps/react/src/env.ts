import { createEnv } from "@t3-oss/env-core";
import { z } from "zod";

export const env = createEnv({
  clientPrefix: "PUBLIC_",
  server: {
    NODE_ENV: z
      .enum(["development", "test", "production"])
      .default("development"),
  },
  client: {
    PUBLIC_SITE_URL: z.string().url().default("http://localhost:5173"),
  },
  runtimeEnv: import.meta.env,
  skipValidation: !!import.meta.env.SKIP_ENV_VALIDATION,
  emptyStringAsUndefined: true,
});
