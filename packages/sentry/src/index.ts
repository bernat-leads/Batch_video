export { env } from "./env";
export { buildSharedConfig } from "./config";
export type { SentrySharedConfig, SharedConfigOptions } from "./config";

export {
  beforeSendSanitize,
  beforeSendSanitizeHeaders,
  sanitizeBody,
  sanitizeHeaders,
} from "./sanitize";
