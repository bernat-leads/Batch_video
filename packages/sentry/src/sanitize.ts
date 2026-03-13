/**
 * Shared Sentry event sanitization utilities.
 *
 * Re-usable `beforeSend` helpers that strip sensitive data from events
 * before they are sent to Sentry.  Import these in your app-level
 * sentry config files.
 */

import type { Event } from "@sentry/core";

/** Headers that should never be sent to Sentry. */
const SENSITIVE_HEADERS = ["authorization", "cookie", "x-forwarded-for"] as const;

/** Body fields that should be redacted. */
const SENSITIVE_BODY_FIELDS = ["password", "token", "secret"] as const;

/**
 * Strip sensitive headers from a Sentry event's request data.
 */
export function sanitizeHeaders(event: Event): void {
  if (!event.request?.headers) return;
  for (const header of SENSITIVE_HEADERS) {
    delete event.request.headers[header];
  }
}

/**
 * Redact known sensitive fields in the request body.
 */
export function sanitizeBody(event: Event): void {
  if (!event.request?.data) return;

  try {
    const data =
      typeof event.request.data === "string"
        ? JSON.parse(event.request.data)
        : event.request.data;

    for (const field of SENSITIVE_BODY_FIELDS) {
      if (data?.[field]) data[field] = "[Filtered]";
    }

    event.request.data =
      typeof event.request.data === "string" ? JSON.stringify(data) : data;
  } catch {
    // If we cannot parse the body, leave it as-is rather than crash.
  }
}

/**
 * A ready-to-use `beforeSend` callback that applies all sanitization.
 *
 * Usage:
 * ```ts
 * Sentry.init({ beforeSend: beforeSendSanitize });
 * ```
 */
export function beforeSendSanitize(event: Event): Event {
  sanitizeHeaders(event);
  sanitizeBody(event);
  return event;
}

/**
 * A lighter `beforeSend` that only strips headers (suitable for client-side
 * configs where there is no request body to redact).
 */
export function beforeSendSanitizeHeaders(event: Event): Event {
  sanitizeHeaders(event);
  return event;
}
