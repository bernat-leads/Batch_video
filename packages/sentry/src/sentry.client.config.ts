import * as Sentry from "@sentry/nextjs";
import { buildSharedConfig } from "./config";
import { beforeSendSanitizeHeaders } from "./sanitize";

const shared = buildSharedConfig();

Sentry.init({
  ...shared,

  // Session Replay — only capture replays when an error occurs
  replaysOnErrorSampleRate: 1.0,
  replaysSessionSampleRate: 0,

  beforeSend: beforeSendSanitizeHeaders,

  integrations: [
    Sentry.replayIntegration({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],
});
