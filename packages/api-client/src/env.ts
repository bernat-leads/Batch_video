import { createEnv } from "@t3-oss/env-core";
import { z } from "zod";

export const env = createEnv({
  clientPrefix: "PUBLIC_",
  client: {
    // Empty string = same origin (production with nginx proxy)
    // Full URL = direct backend (local dev: http://localhost:8000)
    PUBLIC_API_URL: z.string().optional().default(""),
  },
  runtimeEnv: import.meta.env,
  skipValidation: !!import.meta.env.SKIP_ENV_VALIDATION,
});
