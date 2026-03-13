/**
 * Shared Sentry configuration for all JS/TS apps in the monorepo.
 *
 * Each app imports these defaults and merges them with framework-specific
 * options (e.g. @sentry/nextjs integrations).  The Python backend
 * (apps/fastapi) uses its own sentry-sdk — this package is for JS/TS only.
 */

import { env } from "./env";

export interface SentrySharedConfig {
  /** Sentry DSN.  When falsy, Sentry should be disabled. */
  dsn: string | undefined;
  /** Whether Sentry is enabled (derived from DSN presence by default). */
  enabled: boolean;
  /** Runtime environment label sent with every event. */
  environment: string;
  /** Fraction of transactions to sample for performance monitoring. */
  tracesSampleRate: number;
  /** Fraction of profiles to sample (requires tracing). */
  profilesSampleRate: number;
  /** Whether to send default PII (IP address, cookies, etc.). */
  sendDefaultPii: boolean;
}

export interface SharedConfigOptions {
  /** Override environment detection (defaults to NODE_ENV). */
  environment?: string;
  /** Override production traces sample rate (default 0.1). */
  productionTracesSampleRate?: number;
  /** Override development traces sample rate (default 1.0). */
  developmentTracesSampleRate?: number;
  /** Override profiles sample rate (default 0). */
  profilesSampleRate?: number;
  /** Override sendDefaultPii (default false). */
  sendDefaultPii?: boolean;
}

/**
 * Build the shared Sentry configuration object.
 *
 * DSN is read automatically from `NEXT_PUBLIC_SENTRY_DSN` via the package env.
 *
 * Usage (e.g. in `sentry.server.config.ts`):
 * ```ts
 * import * as Sentry from "@sentry/nextjs";
 * import { buildSharedConfig } from "@packages/sentry";
 *
 * Sentry.init({ ...buildSharedConfig() });
 * ```
 */
export function buildSharedConfig(options: SharedConfigOptions = {}): SentrySharedConfig {
  const dsn = env.NEXT_PUBLIC_SENTRY_DSN;
  const environment = options.environment ?? process.env.NODE_ENV ?? "development";
  const isProduction = environment === "production";

  const tracesSampleRate = isProduction
    ? (options.productionTracesSampleRate ?? 0.1)
    : (options.developmentTracesSampleRate ?? 1.0);

  return {
    dsn,
    enabled: !!dsn,
    environment,
    tracesSampleRate,
    profilesSampleRate: options.profilesSampleRate ?? 0,
    sendDefaultPii: options.sendDefaultPii ?? false,
  };
}
