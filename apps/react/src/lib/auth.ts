import type { ErrorType, LoginRequest } from "@packages/api-client";
import { z } from "zod";

export const loginSchema = z.object({
  password: z.string().min(1, "Password is required"),
}) satisfies z.ZodType<LoginRequest>;

export function isUnauthorized(error: unknown): boolean {
  return (error as ErrorType<unknown>)?.response?.status === 401;
}
