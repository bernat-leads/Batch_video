import { createEnv } from "@t3-oss/env-core";
import { z } from "zod";

export const env = createEnv({
  clientPrefix: "PUBLIC_",
  client: {
    PUBLIC_API_URL: z.string().url().default("http://localhost:8000"),
  },
  runtimeEnv: import.meta.env,
  skipValidation: !!import.meta.env.SKIP_ENV_VALIDATION,
  emptyStringAsUndefined: true,
});
