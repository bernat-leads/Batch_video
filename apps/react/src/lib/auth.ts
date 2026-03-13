import { meApiV1AuthMeGet } from "@packages/api-client";
import type { ErrorType, LoginRequest } from "@packages/api-client";
import { redirect } from "@tanstack/react-router";
import { z } from "zod";

export const loginSchema = z.object({
  password: z.string().min(1, "Password is required"),
}) satisfies z.ZodType<LoginRequest>;

export function isUnauthorized(error: unknown): boolean {
  return (error as ErrorType<unknown>)?.response?.status === 401;
}

/**
 * Check if the current session is valid.
 * Redirects to /login if not authenticated.
 * Intended for use in route `beforeLoad` hooks.
 */
export async function requireAuth(pathname: string) {
  if (pathname === "/login") return;

  try {
    await meApiV1AuthMeGet();
  } catch {
    throw redirect({ to: "/login" });
  }
}
