import * as Sentry from "@sentry/nextjs";
import { buildSharedConfig } from "./config";
import { beforeSendSanitize } from "./sanitize";

const shared = buildSharedConfig();

Sentry.init({
  ...shared,
  beforeSend: beforeSendSanitize,
});
