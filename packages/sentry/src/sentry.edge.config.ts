import * as Sentry from "@sentry/nextjs";
import { buildSharedConfig } from "./config";

const shared = buildSharedConfig();

Sentry.init({
  ...shared,
});
