import { z } from "zod";
import type { LoginRequest } from "@packages/api-client";

export const loginSchema = z.object({
  password: z.string().min(1, "Password is required"),
}) satisfies z.ZodType<LoginRequest>;
